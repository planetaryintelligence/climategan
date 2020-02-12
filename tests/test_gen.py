import argparse
import sys
from pathlib import Path

import numpy as np
import torch
from torchsummary import summary

sys.path.append(str(Path(__file__).parent.parent.resolve()))
from omnigan.generator import get_gen
from omnigan.utils import load_opts
from run import print_header


parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", default="config/local_tests.yaml")
args = parser.parse_args()
root = Path(__file__).parent.parent
opts = load_opts(root / args.config, default=root / "shared/defaults.yaml")


if __name__ == "__main__":

    np.random.seed(0)
    torch.manual_seed(0)

    opts = opts.copy()

    batch_size = 2
    latent_space_dims = [256, 32, 32]

    image = torch.Tensor(batch_size, 3, 256, 256).uniform_(-1, 1)

    test_partial_decoder = True
    print_architecture = False
    test_encoder = True
    test_encode_decode = True
    test_translation = True
    test_summary = True

    if test_partial_decoder:
        print_header("test_partial_decoder")
        opts.gen.a.ignore = False
        opts.gen.d.ignore = True
        opts.gen.h.ignore = False
        opts.gen.t.ignore = False
        opts.gen.w.ignore = False
        G = get_gen(opts)
        print("d" in G.decoders)
        print("a" in G.decoders)
        z = torch.randn(batch_size, *latent_space_dims, dtype=torch.float32)
        v = G.decoders["s"](z)
        print(v.shape)
        print(sum(p.numel() for p in G.decoders.parameters()))

    opts.gen.a.ignore = False
    opts.gen.d.ignore = False
    opts.gen.h.ignore = False
    opts.gen.t.ignore = False
    opts.gen.w.ignore = False

    G = get_gen(opts)
    if print_architecture:
        print("DECODERS:", G.decoders)
        print("ENCODER:", G.encoder)

    if test_encoder:
        print_header("test_encoder")
        encoded = G.encode(image)
        print("Latent space dims {}".format(tuple(encoded.shape)[1:]))

    if test_encode_decode:
        print_header("test_encode_decode")
        z = G.encode(image)
        for dec in "adhtw":
            if dec in G.decoders:
                if dec == "t":
                    continue
                if dec == "a":
                    for d in G.decoders[dec]:
                        print(dec, d, G.decoders[dec][d](z).shape)
                else:
                    print(dec, G.decoders[dec](z).shape)

    if test_translation:
        print_header("test_translation use_bit_conditioning")
        opts.gen.t.use_spade = True
        opts.gen.t.use_bit_conditioning = True
        G = get_gen(opts)
        print(G.forward(image, translator="f").shape)

        print_header("test_translation use_spade no use_bit_conditioning")
        opts.gen.t.use_spade = True
        opts.gen.t.use_bit_conditioning = False
        G = get_gen(opts)
        print(G.forward(image, translator="f").shape)

        print_header("test_translation vanilla")
        opts.gen.t.use_spade = False
        opts.gen.t.use_bit_conditioning = False
        G = get_gen(opts)
        print(G.forward(image, translator="f").shape)

    if test_summary:
        print_header("Generator summary no Spades")
        print(summary(G, input_size=(3, 256, 256)))

        print_header("Generator summary Spades")
        opts.gen.t.use_spade = True
        G = get_gen(opts)
        print(summary(G, input_size=(3, 256, 256)))
