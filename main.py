from functools import lru_cache


class VectorClassBuilder:
    def __init__(self, dimensions: int, typeName: str):
        self.dimensions = dimensions
        self.typeName = typeName
        self.axies = 'xyzwvutsrq'
        self.tab_size = 4

        self._buffer: list[str] = []

    def _push(self, *text: str) -> None:
        self._buffer.extend(text)

    def write(self, *text: str, shift: int = 0, newlines: int = 1) -> None:
        if shift != 0: self._push(' ' * (self.tab_size * shift))
        self._push(*text)
        if newlines != 0: self._push('\n' * newlines)

    def result(self) -> str:
        return ''.join(self._buffer)

    def buildConstructorsH(self):
        for dim in range(2, self.dimensions+1):
            self.write("struct ", self.getTypeName(dim), " {")
            self.write("public:")

            # --- Axies --- // float x, y, z, w;
            self.write(f'{self.typeName} ', ', '.join(self.axies[:dim]), ';', shift=1)

            # --- Constructors --- // Vec4(const Vec4& xyzw);
            for subdims in buildLists(dim):
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
            # for resultdim in range(2, self.dimensions+1):
            #     for axies in shit_ahh_funtion(resultdim, dim):
            #         print(f"    {self.getTypeName(resultdim)} ", end='')
            #         print(''.join((list(map(self.axis, axies)))), end='')
            #         print("();")
            #     print()

            self.write("};", newlines=2)
            # --- Out ---
            self.write(self.getTypeName(dim), " operator*(", self.typeName, " scalar, ", self.getTypeNameArg(dim), " vec);")
            self.write(newlines=1)

    
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


def main():
    builder = VectorClassBuilder(4, "float")
    builder.buildConstructorsH()
    print(builder.result(), end='')


# TODO: Shit ahh realization
@lru_cache(maxsize=None)
def buildLists(n: int) -> list[list[int]]:
    if n == 0:
        return []
    result: list[list[int]] = [[n]]
    for i in range(1, n+1):
        for r in buildLists(n-i):
            result.append([i, *r])
    return result

@lru_cache(maxsize=None)
def shit_ahh_funtion(n: int, m: int) -> list[list[int]]:
    if n == 0:
        return [[]]
    result: list[list[int]] = []
    r = shit_ahh_funtion(n-1, m)
    for i in range(1, m+1):
        for j in r:
            result.append([i, *j])
    return result

if __name__ == '__main__':
    main()


