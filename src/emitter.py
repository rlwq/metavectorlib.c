from abc import ABC, abstractmethod
from dataclasses import dataclass
from collections.abc import Iterator


@dataclass(frozen=True)
class EmitterContext:
    dimensions: int
    scalar_type: str
    vector_name_prefix: str = 'Vec'
    matrix_name_prefix: str = 'Matrix' 
    tab_size: int = 4
    axes: str = 'xyzwvutsrqabcdefghijk'

    def axis(self, n: int) -> str:
        return self.axes[n % self.dimensions]

    def vec_type_name(self, d: int) -> str:
        if d == 1: return self.scalar_type
        return f'{self.vector_name_prefix}{d}'

    def vec_link_type_name(self, d: int) -> str:
        if d == 1: return self.scalar_type
        return f'{self.vector_name_prefix}{d}&'
    
    def vec_const_type_name(self, d: int) -> str:
        if d == 1: return self.scalar_type
        return f'const {self.vector_name_prefix}{d}&'

    def matrix_type_name(self, r: int, c: int) -> str:
        return f'{self.matrix_name_prefix}{r}x{c}'

    def matrix_link_type_name(self, r: int, c: int) -> str:
        return f'{self.matrix_name_prefix}{r}x{c}&'
    
    def matrix_const_type_name(self, r: int, c: int) -> str:
        return f'const {self.matrix_name_prefix}{r}x{c}&'


class Emitter(ABC):
    def __init__(self, context: EmitterContext) -> None:
        self._ctx: EmitterContext = context
        self._buffer: list[str] = []
        self._shift: int = 0
        self._do_shift = True

    @property
    def ctx(self) -> EmitterContext:
        return self._ctx

    def shift(self, d: int) -> None:
        self._shift += d

    def format(self) -> str:
        return ''.join(self._buffer)

    def write(self, *text: str, newlines: int = 1, shift: int = 0) -> None:
        if self._shift+shift != 0 and self._do_shift: self._buffer.append(' ' * (self.ctx.tab_size * (self._shift+shift)))
        self._buffer.extend(text)
        if newlines != 0: self._buffer.append('\n' * newlines)
        self._do_shift = newlines > 0

    @abstractmethod
    def build(self) -> None:
        pass


def compositions(n: int) -> Iterator[list[int]]:
    curr = [1] * n
    while curr:
        yield curr.copy()
        d = curr.pop()
        if not curr:
            break
        curr[-1] += 1
        curr.extend([1] * (d-1))
