from src.emitter import Emitter


class MatrixHeaderEmitter(Emitter):
    def writeFields(self, rows: int, cols: int) -> None:
        self.write(self.ctx.scalar_type)
        self.shift(1)
        for r in range(rows):
            for c in range(cols):
                if r == rows-1 and c == cols-1: continue
                self.write(f'm{r}x{c}, ', newlines=0)
            if r != rows-1: self.write()
        self.write(f'm{rows-1}x{cols-1};')
        self.shift(-1)
    
    def writeConstructors(self, rows: int, cols: int) -> None:
        self.write(self.ctx.matrix_type_name(rows, cols), '(', self.ctx.matrix_const_type_name(rows, cols), ' other);')

        self.write(self.ctx.matrix_type_name(rows, cols), '(')
        self.shift(1)
        for r in range(rows):
            for c in range(cols):
                if r == rows-1 and c == cols-1: continue
                self.write(f'{self.ctx.scalar_type} m{r}x{c}, ', newlines=0)
            if r != rows-1: self.write()
        self.shift(-1)
        self.write(f'{self.ctx.scalar_type} m{rows-1}x{cols-1} );')

    def writeAlgebra(self, rows: int, cols: int) -> None:
        for op in '+', '-':
            self.write(self.ctx.matrix_type_name(rows, cols), " operator ", op,
                        " (", self.ctx.matrix_const_type_name(rows, cols), " other) const;")
            self.write(self.ctx.matrix_link_type_name(rows, cols), " operator ", op,
                        "= (", self.ctx.matrix_const_type_name(rows, cols), " other);")

        for op in '=', '!':
            self.write("bool operator ", op,
                        "= (", self.ctx.matrix_const_type_name(rows, cols), " other) const;")

        for op in '*', '/':
            self.write(self.ctx.matrix_type_name(rows, cols), " operator ", op,
                        " (", self.ctx.scalar_type, " scalar) const;")
            self.write(self.ctx.matrix_type_name(rows, cols), "& operator ", op,
                        "= (", self.ctx.scalar_type, " scalar);")
        
        for k in range(2, self.ctx.dimensions+1):
            self.write(self.ctx.matrix_type_name(rows, k), " operator * (", self.ctx.matrix_const_type_name(cols, k), " other) const;")
        self.write(self.ctx.vec_type_name(rows), " operator * (", self.ctx.vec_const_type_name(cols), " other) const;")
        self.write()

    def writeMethods(self, rows: int, cols: int) -> None:
        if rows == cols:
            self.write(self.ctx.scalar_type, " det() const;")
        self.write(self.ctx.matrix_type_name(cols, rows), " transposed () const;")
        self.write()

    def build(self) -> None:
        self.write('#pragma once', newlines=2)

        for rows in range(2, self.ctx.dimensions+1):
            for cols in range(2, self.ctx.dimensions+1):
                self.write('struct ', self.ctx.matrix_type_name(rows, cols), ' {')
                self.shift(1)
                self.write('private:', shift=-1)
                self.writeFields(rows, cols)
                self.write('public:', shift=-1)
                self.writeConstructors(rows, cols)
                self.writeAlgebra(rows, cols)
                self.writeMethods(rows, cols)
                self.shift(-1)
                self.write('};')

                self.write(self.ctx.matrix_type_name(rows, cols), " operator * (", self.ctx.scalar_type,
                    " scalar, ", self.ctx.matrix_const_type_name(rows, cols), " m);")
                
                self.write(self.ctx.vec_type_name(cols), " operator * (", self.ctx.vec_const_type_name(rows), " vec, ",
                           self.ctx.matrix_const_type_name(rows, cols), " m", ");")
                self.write(newlines=2)
