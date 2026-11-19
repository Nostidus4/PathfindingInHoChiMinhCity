"""Explicitly labelled mock visualization demo; not a GA optimization result."""
from pathlib import Path
import numpy as np
from src._mocks import fake_instance, fake_chromosome, fake_history
from src.visualize import plot_history, plot_room_heatmap
from src.export import export_schedule


def main():
    base=Path('results/tv6_demo')
    inst=fake_instance(n_rooms=20, seed=42)
    chrom=fake_chromosome(inst, np.random.default_rng(42))
    plot_history(fake_history(n_gen=120,seed=42), str(base/'figures'/'fitness_MOCK.png'))
    plot_room_heatmap(chrom,inst,str(base/'figures'/'room_heatmap_MOCK.png'))
    export_schedule(chrom,inst,str(base/'schedules'))
    print(f'MOCK only - not a GA result. Files generated at {base.resolve()}')

if __name__=='__main__': main()
