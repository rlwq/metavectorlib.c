from collections.abc import Iterator
from itertools import product


class VectorClassBuilder:
    def __init__(self, dimensions: int, typeName: str):
        self.dimensions = dimensions
        self.typeName = typeName
        self.axies = 'xyzwvutsrqabcdefghijk'
        self.tab_size = 4

        self._header_buffer: list[str] = []
        self._realization_buffer: list[str] = []
        self._buffer: list[str] = self._header_buffer

    def write_header(self) -> None:
        self._buffer = self._header_buffer
    
    def write_realization(self) -> None:
        self._buffer = self._realization_buffer

    def _push(self, *text: str) -> None:
        self._buffer.extend(text)

    def write(self, *text: str, shift: int = 0, newlines: int = 1) -> None:
        if shift != 0: self._push(' ' * (self.tab_size * shift))
        self._push(*text)
        if newlines != 0: self._push('\n' * newlines)

    def header(self) -> str:
        return ''.join(self._header_buffer)

    def realization(self) -> str:
        return ''.join(self._realization_buffer)

    def buildHeader(self):
        self.write_header()
        self.write("#pragma once ", newlines=2)

        for dim in range(2, self.dimensions+1):
            self.write("struct ", self.getTypeName(dim), " {")
            self.write("public:")

            # --- Axies --- // float x, y, z, w;
            self.write(f'{self.typeName} ', ', '.join(self.axies[:dim]), ';', shift=1)

            # --- Constructors --- // Vec4(const Vec4& xyzw);
            for subdims in compositions(dim):
                self.write(self.getTypeName(dim), '(', shift=1, newlines=0)
                
                components = list(map(lambda n: self.getTypeNameArg(n), subdims))
                acc = 0
                for i in range(len(subdims)-1):
                    axies = self.axies[acc:acc+subdims[i]]
                    self.write(components[i], ' ', axies, ", ", newlines=0)
                    acc += subdims[i]

                axies = self.axies[acc:acc+subdims[-1]]
                self.write(components[-1], ' ', axies, ');')
            
            self.write(newlines=1)

            # --- Algebra ---
            for op in '+', '-':
                self.write(self.getTypeName(dim), " operator ", op,
                           " (", self.getTypeNameArg(dim), " other) const;", shift=1)
                self.write(self.getTypeName(dim), "& operator ", op,
                           "= (", self.getTypeNameArg(dim), " other);", shift=1)

            for op in '=', '!':
                self.write("bool operator ", op,
                           "= (", self.getTypeNameArg(dim), " other) const;", shift=1)

            for op in '*', '/':
                self.write(self.getTypeName(dim), " operator ", op,
                           " (", self.typeName, " scalar) const;", shift=1)
                self.write(self.getTypeName(dim), "& operator ", op,
                           "= (", self.typeName, " scalar);", shift=1)

            self.write(newlines=1)

            # --- Other ---
            self.write(self.typeName, " mag() const;", shift=1)
            self.write(self.getTypeName(dim), " normalized() const;", shift=1)
            self.write(self.getTypeName(dim), "& normalize();", shift=1)
            self.write(self.typeName, " dot (", self.getTypeNameArg(dim), " other) const;", shift=1)

            # --- Swizzling ---
            if True:
                for resultdim in range(2, self.dimensions+1):
                    for axies in product(range(1, dim+1), repeat=resultdim):
                        self.write(self.getTypeName(resultdim), ' ',
                                *map(self.axis, axies), "();", shift=1)
                    self.write()

            self.write("};", newlines=2)
            # --- Out ---
            self.write(self.getTypeName(dim), " operator*(", self.typeName, " scalar, ", self.getTypeNameArg(dim), " vec);")
            self.write(newlines=1)

    def buildRealization(self):
        self.write_realization()
        self.write('#include "hahaha"')
        self.write('#include "<cmath>"', newlines=2)

        for dim in range(2, self.dimensions+1):
            # --- Constructors --- // Vec4(const Vec4& xyzw);
            for components in compositions(dim):
                # (float x, float y, float z)
                self.write(self.getTypeName(dim), '::', self.getTypeName(dim), '(', newlines=0)
                acc = 0
                for i in range(len(components)-1):
                    axies = self.axies[acc:acc+components[i]]
                    self.write(self.getTypeNameArg(components[i]), ' ', axies, ", ", newlines=0)
                    acc += components[i]

                axies = self.axies[acc:acc+components[-1]]
                self.write(self.getTypeNameArg(components[-1]), ' ', axies, ') : ', newlines=0)
                
                # x(x.x), y(y.y), z(z.z)
                acc = 0
                for i, component in enumerate(components):
                    axies = self.axies[acc:acc+component]
                    for j, axis in enumerate(self.axies[:component]):
                        self.write(self.axies[acc+j], '(', newlines=0)      
                        if component == 1: self.write(axies, ')', newlines=0)
                        else: self.write(axies, '.', axis, ')', newlines=0)

                        if i != len(components) - 1 or j != len(self.axies[:component]) - 1:
                            self.write(', ', newlines=0)
                    acc += component
                del acc
                self.write(' {}')

            # --- Algebra ---
            for op in '+', '-':
                self.write(self.getTypeName(dim), " ", self.getTypeName(dim), "::operator ", op, " (", 
                            self.getTypeNameArg(dim), " other) const {", shift=0)
                
                self.write("return ", self.getTypeName(dim), "(", shift=1, newlines=0)
                for i in range(dim-1):
                    self.write("this->", self.axies[i], ' ', op, " other.", self.axies[i], ', ', newlines=0)
                self.write("this->", self.axies[dim-1], ' ', op, " other.", self.axies[dim-1], ");")
                self.write('}')
            
            for op in '+', '-':
                self.write(self.getTypeName(dim), "& ", self.getTypeName(dim), "::operator ", op, "= (", 
                            self.getTypeNameArg(dim), " other) {", shift=0)
                
                for i in range(dim):
                    self.write(self.axies[i], ' ', op, "= other.", self.axies[i], ';', shift=1)

                self.write("return *this;", shift=1)
                self.write('}')
            
            for op, l_op in ('=', '&&'), ('!', '||'):
                self.write("bool ", self.getTypeName(dim), "::operator ", op, "= (", 
                            self.getTypeNameArg(dim), " other) const {", shift=0)
                
                self.write("return ", shift=1, newlines=0)
                for i in range(dim-1):
                    self.write("this->", self.axies[i], ' ', op, "= other.", self.axies[i], ' ', l_op, ' ', newlines=0)
                self.write("this->", self.axies[dim-1], ' ', op, "= other.", self.axies[dim-1], ';')
                self.write('}')

            for op in '*', '/':
                self.write(self.getTypeName(dim), " ", self.getTypeName(dim), "::operator ", op, " (", 
                            self.typeName, " scalar) const {", shift=0)
                
                self.write("return ", self.getTypeName(dim), "(", shift=1, newlines=0)
                for i in range(dim-1):
                    self.write("this->", self.axies[i], ' ', op, ' scalar, ', newlines=0)
                self.write("this->", self.axies[dim-1], ' ', op, ' scalar);')
                self.write('}')
            
            for op in '*', '/':
                self.write(self.getTypeName(dim), "& ", self.getTypeName(dim), "::operator ", op, "= (", 
                            self.typeName, " scalar) {", shift=0)
                
                for i in range(dim):
                    self.write(self.axies[i], ' ', op, "= scalar;", shift=1)

                self.write("return *this;", shift=1)
                self.write('}')

            
            self.write()

            # --- Other ---
            self.write(self.typeName, ' ', self.getTypeName(dim), "::mag() const {")
            
            self.write("return sqrt(", shift=1, newlines=0)
            for i in range(dim-1):
                self.write(self.axies[i], '*', self.axies[i], ' + ', newlines=0)
            self.write(self.axies[dim-1], '*', self.axies[dim-1], ');')

            self.write('}', newlines=2)


            self.write(self.getTypeName(dim), ' ', self.getTypeName(dim), "::normalized() const {")
            self.write("return *this / this->mag();", shift=1)
            self.write('}', newlines=2)

            self.write(self.getTypeName(dim), '& ', self.getTypeName(dim), "::normalize() {")
            self.write("*this /= this->mag();", shift=1)
            self.write("return *this;", shift=1)
            self.write('}', newlines=2)

            self.write(self.typeName, " ", self.getTypeName(dim), "::dot (", 
                            self.getTypeNameArg(dim), " other) const {", shift=0)
                
            self.write("return ", shift=1, newlines=0)
            for i in range(dim-1):
                self.write("this->", self.axies[i], '*other.', self.axies[i], ' + ', newlines=0)
            self.write("this->", self.axies[dim-1], '*other.', self.axies[dim-1], ';')
            self.write('}', newlines=2)

            # --- Swizzling ---
            # --- Out ---
            self.write(self.getTypeName(dim), " operator * (", 
                            self.typeName, " scalar, ", self.getTypeNameArg(dim), " vec) {", shift=0)
            self.write("return vec * scalar;", shift=1)
            self.write('}', newlines=2)
    
    def axis(self, n: int) -> str:
        return self.axies[n-1]

    def getTypeName(self, n: int) -> str:
        if n == 1:
            return self.typeName
        return f"Vec{n}"
    
    def getTypeNameArg(self, n: int) -> str:
        if n == 1:
            return self.typeName
        return f"const Vec{n}&"

def compositions(n: int) -> Iterator[list[int]]:
    curr = [1] * n
    while curr:
        yield curr.copy()
        d = curr.pop()
        if not curr:
            break
        curr[-1] += 1
        curr.extend([1] * (d-1))

def main():
    builder = VectorClassBuilder(4, "float")
    with open("./.src/test.h", "w") as header:
        builder.buildHeader()
        header.write(builder.header())
    
    with open("./.src/test.cpp", "w") as realization:
        builder.buildRealization()
        realization.write(builder.realization())

if __name__ == '__main__':
    main()
