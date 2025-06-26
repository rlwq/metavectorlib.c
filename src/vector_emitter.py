from src.emitter import Emitter, compositions
from itertools import product


class VectorHeaderEmitter(Emitter):
    def writeConstructors(self, d: int) -> None:
        for subdims in compositions(d):
            self.write(self.ctx.vec_type_name(d), '(', newlines=0)
            
            acc = 0
            for i in range(len(subdims)-1):
                axes = self.ctx.axes[acc:acc+subdims[i]]
                self.write(self.ctx.vec_const_type_name(subdims[i]), ' ', axes, ", ", newlines=0)
                acc += subdims[i]

            axes = self.ctx.axes[acc:acc+subdims[-1]]
            self.write(self.ctx.vec_const_type_name(subdims[-1]), ' ', axes, ');')
        
        self.write()

    def writeAlgebra(self, d: int) -> None:
        for op in '+', '-':
            self.write(self.ctx.vec_type_name(d), " operator ", op,
                        " (", self.ctx.vec_const_type_name(d), " other) const;")
            self.write(self.ctx.vec_link_type_name(d), " operator ", op,
                        "= (", self.ctx.vec_const_type_name(d), " other);")

        for op in '=', '!':
            self.write("bool operator ", op,
                        "= (", self.ctx.vec_const_type_name(d), " other) const;")

        for op in '*', '/':
            self.write(self.ctx.vec_type_name(d), " operator ", op,
                        " (", self.ctx.scalar_type, " scalar) const;")
            self.write(self.ctx.vec_type_name(d), "& operator ", op,
                        "= (", self.ctx.scalar_type, " scalar);")

        self.write()

    def writeMethods(self, d: int) -> None:
        self.write(self.ctx.scalar_type, " mag() const;")
        self.write(self.ctx.vec_type_name(d), " normalized() const;")
        self.write(self.ctx.vec_type_name(d), "& normalize();")
        self.write(self.ctx.scalar_type, " dot (", self.ctx.vec_const_type_name(d), " other) const;")
        self.write()

    def writeSwizzling(self, d: int) -> None:
        for resultdim in range(2, d+1):
            for axes in product(range(d), repeat=resultdim):
                self.write(self.ctx.vec_type_name(resultdim), ' ', newlines=0)
                self.write(*map(self.ctx.axis, axes), "() const;")
            self.write()

    def build(self) -> None:
        self.write("#pragma once ", newlines=2)

        for dim in range(2, self.ctx.dimensions+1):
            self.write("struct ", self.ctx.vec_type_name(dim), " {")
            self.write("public:")

            self.shift(1)
            self.write(f'{self.ctx.scalar_type} ', ', '.join(self.ctx.axes[:dim]), ';') # --- Axes --- // float x, y, z, w;
            self.writeConstructors(dim)
            self.writeAlgebra(dim)
            self.writeMethods(dim)
            # self.writeSwizzling(dim)
            self.shift(-1)
            self.write("};", newlines=2)

            self.write(self.ctx.vec_type_name(dim), " operator*(", self.ctx.scalar_type,
                       " scalar, ", self.ctx.vec_const_type_name(dim), " vec);")
            self.write()


class ImplVectorEmitter(Emitter):
    def writeConstructors(self, d: int) -> None:
        for components in compositions(d):
            self.write(self.ctx.vec_type_name(d), '::', self.ctx.vec_type_name(d), '(', newlines=0)
            acc = 0
            for i in range(len(components)-1):
                axes = self.ctx.axes[acc:acc+components[i]]
                self.write(self.ctx.vec_const_type_name(components[i]), ' ', axes, ", ", newlines=0)
                acc += components[i]

            axes = self.ctx.axes[acc:acc+components[-1]]
            self.write(self.ctx.vec_const_type_name(components[-1]), ' ', axes, ') : ', newlines=0)
            
            # x(x.x), y(y.y), z(z.z)
            acc = 0
            for i, component in enumerate(components):
                axes = self.ctx.axes[acc:acc+component]
                for j, axis in enumerate(self.ctx.axes[:component]):
                    self.write(self.ctx.axes[acc+j], '(', newlines=0)      
                    if component == 1: self.write(axes, ')', newlines=0)
                    else: self.write(axes, '.', axis, ')', newlines=0)

                    if i != len(components) - 1 or j != len(self.ctx.axes[:component]) - 1:
                        self.write(', ', newlines=0)
                acc += component
            del acc
            self.write(' {}')

    
    def writeAlgebra(self, d: int) -> None:
        for op in '+', '-':
            self.write(self.ctx.vec_type_name(d), " ", self.ctx.vec_type_name(d), "::operator ", op, " (", 
                        self.ctx.vec_const_type_name(d), " other) const {")
            
            self.write("return ", self.ctx.vec_type_name(d), "(", shift=1, newlines=0)
            for i in range(d-1):
                self.write("this->", self.ctx.axis(i), ' ', op, " other.", self.ctx.axis(i), ', ', newlines=0)
            self.write("this->", self.ctx.axis(d-1), ' ', op, " other.", self.ctx.axis(d-1), ");")
            self.write('}')
        
        for op in '+', '-':
            self.write(self.ctx.vec_type_name(d), "& ", self.ctx.vec_type_name(d), "::operator ", op, "= (", 
                        self.ctx.vec_const_type_name(d), " other) {")
            
            self.shift(1)
            for i in range(d):
                self.write(self.ctx.axis(i), ' ', op, "= other.", self.ctx.axis(i), ';')
            self.write("return *this;")
            self.shift(-1)
            
            self.write('}')
        
        for op, l_op in ('=', '&&'), ('!', '||'):
            self.write("bool ", self.ctx.vec_type_name(d), "::operator ", op, "= (", 
                        self.ctx.vec_const_type_name(d), " other) const {")
            
            self.write("return ", shift=1, newlines=0)
            for i in range(d-1):
                self.write("this->", self.ctx.axis(i), ' ', op, "= other.", self.ctx.axis(i), ' ', l_op, ' ', newlines=0)
            self.write("this->", self.ctx.axis(d-1), ' ', op, "= other.", self.ctx.axis(d-1), ';')
            self.write('}')

        for op in '*', '/':
            self.write(self.ctx.vec_type_name(d), " ", self.ctx.vec_type_name(d), "::operator ", op, " (", 
                        self.ctx.scalar_type, " scalar) const {")
            self.shift(1)
            self.write("return ", self.ctx.vec_type_name(d), "(", newlines=0)
            for i in range(d-1):
                self.write("this->", self.ctx.axis(i), ' ', op, ' scalar, ', newlines=0)
            self.write("this->", self.ctx.axis(d-1), ' ', op, ' scalar);')
            self.shift(-1)
            self.write('}')
        
        for op in '*', '/':
            self.write(self.ctx.vec_type_name(d), "& ", self.ctx.vec_type_name(d), "::operator ", op, "= (", 
                        self.ctx.scalar_type, " scalar) {")
            
            self.shift(1)
            for i in range(d):
                self.write(self.ctx.axis(i), ' ', op, "= scalar;")
            self.write("return *this;")
            self.shift(-1)
            self.write('}')
        
        self.write()

    def writeMethods(self, d: int) -> None:
        self.write(self.ctx.scalar_type, ' ', self.ctx.vec_type_name(d), "::mag() const {")
        
        self.shift(1)
        self.write("return sqrt(", newlines=0)
        for i in range(d-1):
            self.write(self.ctx.axis(i), '*', self.ctx.axis(i), ' + ', newlines=0)
        self.write(self.ctx.axis(d-1), '*', self.ctx.axis(d-1), ');')
        self.shift(-1)

        self.write('}', newlines=2)


        self.write(self.ctx.vec_type_name(d), ' ', self.ctx.vec_type_name(d), "::normalized() const {")
        self.write("return *this / this->mag();", shift=1)
        self.write('}', newlines=2)

        self.write(self.ctx.vec_type_name(d), '& ', self.ctx.vec_type_name(d), "::normalize() {")
        self.write("*this /= this->mag();", shift=1)
        self.write("return *this;", shift=1)
        self.write('}', newlines=2)

        self.write(self.ctx.scalar_type, " ", self.ctx.vec_type_name(d), "::dot (", 
                        self.ctx.vec_const_type_name(d), " other) const {")
        
        self.write("return ", newlines=0, shift=1)

        for i in range(d-1):
            self.write("this->", self.ctx.axis(i), '*other.', self.ctx.axis(i), ' + ', newlines=0)
        self.write("this->", self.ctx.axis(d-1), '*other.', self.ctx.axis(d-1), ';')
        self.write('}', newlines=2)

    def writeSwizzling(self, d: int) -> None:
        for resultdim in range(2, d+1):
            for axes in product(range(d), repeat=resultdim):
                used_axes = list(map(self.ctx.axis, axes))
                self.write(self.ctx.vec_type_name(resultdim), ' ', self.ctx.vec_type_name(resultdim), '::',
                        *used_axes, "() const { ", newlines=0)
                self.write("return ", self.ctx.vec_type_name(resultdim), '(', newlines=0)
                self.write(', '.join(used_axes), '); }')
            self.write()

    def build(self) -> None:
        self.write(f'#include "vector{self.ctx.dimensions}.h"') # TODO: to be rewritten
        self.write('#include <cmath>', newlines=2)

        for d in range(2, self.ctx.dimensions+1):
            self.writeConstructors(d)
            self.writeAlgebra(d)
            self.writeMethods(d)
            # self.writeSwizzling(d)
            
            self.write(self.ctx.vec_type_name(d), " operator * (", 
                            self.ctx.scalar_type, " scalar, ", self.ctx.vec_const_type_name(d), " vec) {")
            self.write("return vec * scalar;", shift=1)
            self.write('}')

# TODO: Rewrite swizzling
# maybe something like zyx(vec)