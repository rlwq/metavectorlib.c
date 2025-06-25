from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import product

from time import time

@dataclass(frozen=True)
class BuilderContext:
    dimensions: int
    scalar_type: str
    tab_size: int = 4
    type_name_prefix: str = 'Vec' 
    axes: str = 'xyzwvutsrqabcdefghijk'

    def axis(self, n: int) -> str:
        return self.axes[n % self.dimensions]

    def type_name(self, d: int) -> str:
        if d == 1: return self.scalar_type
        return f'{self.type_name_prefix}{d}'

    def link_type_name(self, d: int) -> str:
        if d == 1: return self.scalar_type
        return f'{self.type_name_prefix}{d}&'
    
    def const_type_name(self, d: int) -> str:
        if d == 1: return self.scalar_type
        return f'const {self.type_name_prefix}{d}&'


class Builder(ABC):
    def __init__(self, context: BuilderContext) -> None:
        self._ctx: BuilderContext = context
        self._buffer: list[str] = []
        self._shift: int = 0
        self._do_shift = True

    @property
    def ctx(self) -> BuilderContext:
        return self._ctx

    def shift(self, d: int) -> None:
        self._shift += d

    def format(self) -> str:
        return ''.join(self._buffer)

    def write(self, *text: str, newlines: int = 1) -> None:
        if self._shift != 0 and self._do_shift: self._buffer.append(' ' * (self.ctx.tab_size * self._shift))
        self._buffer.extend(text)
        if newlines != 0: self._buffer.append('\n' * newlines)
        self._do_shift = newlines > 0

    @abstractmethod
    def build(self) -> None:
        pass

class ImplBuilder(Builder):
    def writeConstructors(self, d: int) -> None:
        for components in compositions(d):
            self.write(self.ctx.type_name(d), '::', self.ctx.type_name(d), '(', newlines=0)
            acc = 0
            for i in range(len(components)-1):
                axes = self.ctx.axes[acc:acc+components[i]]
                self.write(self.ctx.const_type_name(components[i]), ' ', axes, ", ", newlines=0)
                acc += components[i]

            axes = self.ctx.axes[acc:acc+components[-1]]
            self.write(self.ctx.const_type_name(components[-1]), ' ', axes, ') : ', newlines=0)
            
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
            self.write(self.ctx.type_name(d), " ", self.ctx.type_name(d), "::operator ", op, " (", 
                        self.ctx.const_type_name(d), " other) const {")
            
            self.shift(1)
            self.write("return ", self.ctx.type_name(d), "(", newlines=0)
            self.shift(-1)
            for i in range(d-1):
                self.write("this->", self.ctx.axis(i), ' ', op, " other.", self.ctx.axis(i), ', ', newlines=0)
            self.write("this->", self.ctx.axis(d-1), ' ', op, " other.", self.ctx.axis(d-1), ");")
            self.write('}')
        
        for op in '+', '-':
            self.write(self.ctx.type_name(d), "& ", self.ctx.type_name(d), "::operator ", op, "= (", 
                        self.ctx.const_type_name(d), " other) {")
            
            self.shift(1)
            for i in range(d):
                self.write(self.ctx.axis(i), ' ', op, "= other.", self.ctx.axis(i), ';')
            self.write("return *this;")
            self.shift(-1)
            
            self.write('}')
        
        for op, l_op in ('=', '&&'), ('!', '||'):
            self.write("bool ", self.ctx.type_name(d), "::operator ", op, "= (", 
                        self.ctx.const_type_name(d), " other) const {")
            
            self.shift(1)
            self.write("return ", newlines=0)
            self.shift(-1)
            for i in range(d-1):
                self.write("this->", self.ctx.axis(i), ' ', op, "= other.", self.ctx.axis(i), ' ', l_op, ' ', newlines=0)
            self.write("this->", self.ctx.axis(d-1), ' ', op, "= other.", self.ctx.axis(d-1), ';')
            self.write('}')

        for op in '*', '/':
            self.write(self.ctx.type_name(d), " ", self.ctx.type_name(d), "::operator ", op, " (", 
                        self.ctx.scalar_type, " scalar) const {")
            self.shift(1)
            self.write("return ", self.ctx.type_name(d), "(", newlines=0)
            for i in range(d-1):
                self.write("this->", self.ctx.axis(i), ' ', op, ' scalar, ', newlines=0)
            self.write("this->", self.ctx.axis(d-1), ' ', op, ' scalar);')
            self.shift(-1)
            self.write('}')
        
        for op in '*', '/':
            self.write(self.ctx.type_name(d), "& ", self.ctx.type_name(d), "::operator ", op, "= (", 
                        self.ctx.scalar_type, " scalar) {")
            
            self.shift(1)
            for i in range(d):
                self.write(self.ctx.axis(i), ' ', op, "= scalar;")
            self.write("return *this;")
            self.shift(-1)
            self.write('}')
        
        self.write()

    def writeMethods(self, d: int) -> None:
        self.write(self.ctx.scalar_type, ' ', self.ctx.type_name(d), "::mag() const {")
        
        self.shift(1)
        self.write("return sqrt(", newlines=0)
        for i in range(d-1):
            self.write(self.ctx.axis(i), '*', self.ctx.axis(i), ' + ', newlines=0)
        self.write(self.ctx.axis(d-1), '*', self.ctx.axis(d-1), ');')
        self.shift(-1)

        self.write('}', newlines=2)


        self.write(self.ctx.type_name(d), ' ', self.ctx.type_name(d), "::normalized() const {")
        self.shift(1)
        self.write("return *this / this->mag();")
        self.shift(-1)
        self.write('}', newlines=2)

        self.write(self.ctx.type_name(d), '& ', self.ctx.type_name(d), "::normalize() {")
        self.shift(1)
        self.write("*this /= this->mag();")
        self.write("return *this;")
        self.shift(-1)
        self.write('}', newlines=2)

        self.write(self.ctx.scalar_type, " ", self.ctx.type_name(d), "::dot (", 
                        self.ctx.const_type_name(d), " other) const {")
        
        self.shift(1)
        self.write("return ", newlines=0)
        self.shift(-1)
        for i in range(d-1):
            self.write("this->", self.ctx.axis(i), '*other.', self.ctx.axis(i), ' + ', newlines=0)
        self.write("this->", self.ctx.axis(d-1), '*other.', self.ctx.axis(d-1), ';')
        self.write('}', newlines=2)

    def writeSwizzling(self, d: int) -> None:
        for resultdim in range(2, self.ctx.dimensions+1):
            for axies in product(range(d), repeat=resultdim):
                self.write(self.ctx.type_name(resultdim), ' ', self.ctx.type_name(resultdim), '::',
                        *map(self.ctx.axis, axies), "() const { ", newlines=0)
                self.write("return ", self.ctx.type_name(resultdim), '(', newlines=0)
                self.write(', '.join(map(self.ctx.axis, axies)), '); }')

    def build(self) -> None:
        self.write('#include "hahaha"')
        self.write('#include "<cmath>"', newlines=2)

        for d in range(2, self.ctx.dimensions+1):
            self.writeConstructors(d)
            self.writeAlgebra(d)
            self.writeMethods(d)
            self.writeSwizzling(d)
            
            self.write(self.ctx.type_name(d), " operator * (", 
                            self.ctx.scalar_type, " scalar, ", self.ctx.const_type_name(d), " vec) {")
            self.shift(1)
            self.write("return vec * scalar;")
            self.shift(-1)
            self.write('}', newlines=2)


class HeaderBuilder(Builder):
    def writeConstructors(self, d: int) -> None:
        for subdims in compositions(d):
            self.write(self.ctx.type_name(d), '(', newlines=0)
            
            acc = 0
            for i in range(len(subdims)-1):
                axes = self.ctx.axes[acc:acc+subdims[i]]
                self.write(self.ctx.const_type_name(subdims[i]), ' ', axes, ", ", newlines=0)
                acc += subdims[i]

            axes = self.ctx.axes[acc:acc+subdims[-1]]
            self.write(self.ctx.const_type_name(subdims[-1]), ' ', axes, ');')
        
        self.write(newlines=1)

    def writeAlgebra(self, d: int) -> None:
        for op in '+', '-':
            self.write(self.ctx.type_name(d), " operator ", op,
                        " (", self.ctx.const_type_name(d), " other) const;")
            self.write(self.ctx.link_type_name(d), " operator ", op,
                        "= (", self.ctx.const_type_name(d), " other);")

        for op in '=', '!':
            self.write("bool operator ", op,
                        "= (", self.ctx.const_type_name(d), " other) const;")

        for op in '*', '/':
            self.write(self.ctx.type_name(d), " operator ", op,
                        " (", self.ctx.scalar_type, " scalar) const;")
            self.write(self.ctx.type_name(d), "& operator ", op,
                        "= (", self.ctx.scalar_type, " scalar);")

        self.write(newlines=1)

    def writeMethods(self, d: int) -> None:
        self.write(self.ctx.scalar_type, " mag() const;")
        self.write(self.ctx.type_name(d), " normalized() const;")
        self.write(self.ctx.type_name(d), "& normalize();")
        self.write(self.ctx.scalar_type, " dot (", self.ctx.const_type_name(d), " other) const;")

    def writeSwizzling(self, d: int) -> None:
        for resultdim in range(2, self.ctx.dimensions+1):
            for axes in product(range(d), repeat=resultdim):
                self.write(self.ctx.type_name(resultdim), ' ', newlines=0)
                self.write(*map(self.ctx.axis, axes), "() const;")
            self.write()

    def build(self) -> None:
        self.write("#pragma once ", newlines=2)

        for dim in range(2, self.ctx.dimensions+1):
            self.write("struct ", self.ctx.type_name(dim), " {")
            self.write("public:")

            # --- Axes --- // float x, y, z, w;
            self.shift(1)
            self.write(f'{self.ctx.scalar_type} ', ', '.join(self.ctx.axes[:dim]), ';')
            self.writeConstructors(dim)
            self.writeAlgebra(dim)
            self.writeMethods(dim)
            self.writeSwizzling(dim)
            self.shift(-1)
            self.write("};", newlines=2)

            self.write(self.ctx.type_name(dim), " operator*(", self.ctx.scalar_type,
                       " scalar, ", self.ctx.const_type_name(dim), " vec);")
            self.write(newlines=1)


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
    context = BuilderContext(3, 'float')
    h_builder = HeaderBuilder(context)
    i_builder = ImplBuilder(context)

    begin_time = time()

    h_builder.build()
    with open("./.src/new.h", "w") as header:
        header.write(h_builder.format())

    header_time = time()

    print(f"Header generated in {header_time - begin_time:0.4f} seconds")


    i_builder.build()
    with open("./.src/new.cpp", "w") as impl:
        impl.write(i_builder.format())

    impl_time = time()

    print(f"Impementation generated in {impl_time - header_time:0.4f} seconds")

if __name__ == '__main__':
    main()
