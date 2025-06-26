from time import time
from src.vector_emitter import VectorHeaderEmitter, ImplVectorEmitter
from src.matrix_emitter import MatrixHeaderEmitter
from src.emitter import EmitterContext


def main():
    d = 7
    ctx = EmitterContext(d, 'float')
    hv_builder = VectorHeaderEmitter(ctx)
    iv_builder = ImplVectorEmitter(ctx)
    hm_builder = MatrixHeaderEmitter(ctx)

    begin_time = time()

    hv_builder.build()
    hm_builder.build()
    with open(f"./.generated/vector{d}.h", "w") as header:
        header.write(hv_builder.format())
        # header.write(hm_builder.format())

    header_time = time()

    print(f"Header generated in {header_time - begin_time:0.4f} seconds")


    iv_builder.build()
    with open(f"./.generated/vector{d}.cpp", "w") as impl:
        impl.write(iv_builder.format())

    impl_time = time()

    print(f"Impementation generated in {impl_time - header_time:0.4f} seconds")

if __name__ == '__main__':
    main()
