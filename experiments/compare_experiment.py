import csv
import math
import random
import string
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable


CAPACITY = 4090
SEED = 20261121
LOAD_FACTORS = tuple(step / 10 for step in range(1, 10))
TOKEN_CHARACTERS = string.ascii_letters + string.digits
CSV_PATH = REPOSITORY_ROOT / "experiments" / "comparison_results.csv"
SVG_PATH = REPOSITORY_ROOT / "experiments" / "comparison_results.svg"


def random_url(rng):
    host = "".join(rng.choices(TOKEN_CHARACTERS, k=16))
    path = "".join(rng.choices(TOKEN_CHARACTERS, k=24))
    return f"https://{host}.example/{path}"


def collect_result(target_load, rng):
    entry_count = round(CAPACITY * target_load)
    chaining_table = HashTable(capacity=CAPACITY, max_load=None)
    probing_table = LinearProbingHashTable(capacity=CAPACITY, max_load=None)
    inserted_urls = []

    while len(inserted_urls) < entry_count:
        url = random_url(rng)
        if chaining_table.get(url) is None:
            value = len(inserted_urls)
            chaining_table.set(url, value)
            probing_table.set(url, value)
            inserted_urls.append(url)

    if (
        chaining_table.capacity != probing_table.capacity
        or chaining_table.capacity != CAPACITY
        or len(chaining_table) != len(probing_table)
        or len(chaining_table) != entry_count
    ):
        raise RuntimeError("comparison tables must have the same size and entries")

    successful_comparisons = {"chaining": 0, "linear_probing": 0}
    for url in inserted_urls:
        chain_value, chain_count = chaining_table.get_with_comparisons(url)
        probe_value, probe_count = probing_table.get_with_comparisons(url)
        if chain_value != probe_value:
            raise RuntimeError("hash table implementations returned different values")
        successful_comparisons["chaining"] += chain_count
        successful_comparisons["linear_probing"] += probe_count

    unsuccessful_comparisons = {"chaining": 0, "linear_probing": 0}
    for _ in inserted_urls:
        url = random_url(rng)
        while chaining_table.get(url) is not None:
            url = random_url(rng)

        chain_value, chain_count = chaining_table.get_with_comparisons(url)
        probe_value, probe_count = probing_table.get_with_comparisons(url)
        if chain_value is not None or probe_value is not None:
            raise RuntimeError("a missing URL was found in a hash table")
        unsuccessful_comparisons["chaining"] += chain_count
        unsuccessful_comparisons["linear_probing"] += probe_count

    query_count = len(inserted_urls)
    load_factor = query_count / CAPACITY
    return {
        "load_factor": load_factor,
        "table_capacity": CAPACITY,
        "entries": query_count,
        "chaining_successful_average": (
            successful_comparisons["chaining"] / query_count
        ),
        "chaining_successful_theory": 1 + load_factor / 2,
        "linear_probing_successful_average": (
            successful_comparisons["linear_probing"] / query_count
        ),
        "linear_probing_successful_theory": (
            0.5 * (1 + 1 / (1 - load_factor))
        ),
        "chaining_unsuccessful_average": (
            unsuccessful_comparisons["chaining"] / query_count
        ),
        "chaining_unsuccessful_theory": load_factor,
        "linear_probing_unsuccessful_average": (
            unsuccessful_comparisons["linear_probing"] / query_count
        ),
        "linear_probing_unsuccessful_theory": (
            0.5 * (1 + 1 / (1 - load_factor) ** 2)
        ),
    }


def write_csv(results):
    fields = (
        "load_factor",
        "table_capacity",
        "entries",
        "chaining_successful_average_comparisons",
        "chaining_successful_theory_comparisons",
        "chaining_unsuccessful_average_comparisons",
        "chaining_unsuccessful_theory_comparisons",
        "linear_probing_successful_average_comparisons",
        "linear_probing_successful_theory_comparisons",
        "linear_probing_unsuccessful_average_comparisons",
        "linear_probing_unsuccessful_theory_comparisons",
    )
    with CSV_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "load_factor": f"{result['load_factor']:.6f}",
                    "table_capacity": result["table_capacity"],
                    "entries": result["entries"],
                    "chaining_successful_average_comparisons": (
                        f"{result['chaining_successful_average']:.6f}"
                    ),
                    "chaining_successful_theory_comparisons": (
                        f"{result['chaining_successful_theory']:.6f}"
                    ),
                    "chaining_unsuccessful_average_comparisons": (
                        f"{result['chaining_unsuccessful_average']:.6f}"
                    ),
                    "chaining_unsuccessful_theory_comparisons": (
                        f"{result['chaining_unsuccessful_theory']:.6f}"
                    ),
                    "linear_probing_successful_average_comparisons": (
                        f"{result['linear_probing_successful_average']:.6f}"
                    ),
                    "linear_probing_successful_theory_comparisons": (
                        f"{result['linear_probing_successful_theory']:.6f}"
                    ),
                    "linear_probing_unsuccessful_average_comparisons": (
                        f"{result['linear_probing_unsuccessful_average']:.6f}"
                    ),
                    "linear_probing_unsuccessful_theory_comparisons": (
                        f"{result['linear_probing_unsuccessful_theory']:.6f}"
                    ),
                }
            )


def write_svg(results):
    width, height = 960, 610
    left, right, top, bottom = 82, 30, 160, 62
    chart_width = width - left - right
    chart_height = height - top - bottom
    x_min, x_max = 0.1, 0.9
    value_fields = tuple(
        f"{table}_{outcome}_{kind}"
        for table in ("chaining", "linear_probing")
        for outcome in ("successful", "unsuccessful")
        for kind in ("average", "theory")
    )
    largest_value = max(
        result[field] for result in results for field in value_fields
    )
    y_max = max(1, math.ceil(largest_value))

    def x_position(load_factor):
        return left + (load_factor - x_min) / (x_max - x_min) * chart_width

    def y_position(value):
        return top + chart_height - value / y_max * chart_height

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        "<title>Chaining and linear probing comparison</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="480" y="30" text-anchor="middle" font-family="sans-serif" '
        'font-size="20">Measured and theoretical lookup comparisons</text>',
        '<text x="480" y="49" text-anchor="middle" font-family="sans-serif" '
        f'font-size="12">Both tables: {CAPACITY} slots; identical keys</text>',
    ]

    y_step = max(1, math.ceil(y_max / 6))
    y_ticks = list(range(0, y_max + 1, y_step))
    if y_ticks[-1] != y_max:
        y_ticks.append(y_max)
    for tick in y_ticks:
        y = y_position(tick)
        svg.extend(
            [
                f'<line x1="{left}" y1="{y:.2f}" x2="{width - right}" '
                f'y2="{y:.2f}" stroke="#dddddd"/>',
                f'<text x="{left - 12}" y="{y + 5:.2f}" text-anchor="end" '
                f'font-family="sans-serif" font-size="12">{tick}</text>',
            ]
        )

    for step in range(1, 10):
        target_load = step / 10
        x = x_position(target_load)
        svg.extend(
            [
                f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" '
                f'y2="{top + chart_height}" stroke="#eeeeee"/>',
                f'<text x="{x:.2f}" y="{top + chart_height + 22}" '
                f'text-anchor="middle" font-family="sans-serif" '
                f'font-size="12">{target_load:.1f}</text>',
            ]
        )

    svg.extend(
        [
            f'<line x1="{left}" y1="{top + chart_height}" x2="{width - right}" '
            f'y2="{top + chart_height}" stroke="#333333"/>',
            f'<line x1="{left}" y1="{top}" x2="{left}" '
            f'y2="{top + chart_height}" stroke="#333333"/>',
            f'<text x="{left + chart_width / 2}" y="{height - 18}" '
            'text-anchor="middle" font-family="sans-serif" font-size="14">'
            "Load factor (α)</text>",
            f'<text x="22" y="{top + chart_height / 2}" text-anchor="middle" '
            'font-family="sans-serif" font-size="14" '
            f'transform="rotate(-90 22 {top + chart_height / 2})">'
            "Average key comparisons / slots inspected</text>",
        ]
    )

    series = (
        (
            "chaining_successful_average",
            "#1769aa",
            "Chaining successful (measured)",
            True,
        ),
        (
            "chaining_successful_theory",
            "#1769aa",
            "Chaining successful (theory)",
            False,
        ),
        (
            "chaining_unsuccessful_average",
            "#4c9f70",
            "Chaining unsuccessful (measured)",
            True,
        ),
        (
            "chaining_unsuccessful_theory",
            "#4c9f70",
            "Chaining unsuccessful (theory)",
            False,
        ),
        (
            "linear_probing_successful_average",
            "#d1495b",
            "Linear probing successful (measured)",
            True,
        ),
        (
            "linear_probing_successful_theory",
            "#d1495b",
            "Linear probing successful (theory)",
            False,
        ),
        (
            "linear_probing_unsuccessful_average",
            "#f28e2b",
            "Linear probing unsuccessful (measured)",
            True,
        ),
        (
            "linear_probing_unsuccessful_theory",
            "#f28e2b",
            "Linear probing unsuccessful (theory)",
            False,
        ),
    )
    legend_positions = tuple(
        (90 + (index % 2) * 430, 67 + (index // 2) * 22)
        for index in range(len(series))
    )
    for (field, color, label, measured), (legend_x, legend_y) in zip(
        series, legend_positions
    ):
        points = " ".join(
            f"{x_position(result['load_factor']):.2f},"
            f"{y_position(result[field]):.2f}"
            for result in results
        )
        dash = "" if measured else ' stroke-dasharray="7 5"'
        svg.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" '
            f'stroke-width="2"{dash}/>'
        )
        if measured:
            for result in results:
                svg.append(
                    f'<circle cx="{x_position(result["load_factor"]):.2f}" '
                    f'cy="{y_position(result[field]):.2f}" r="2.5" '
                    f'fill="{color}"/>'
                )
        svg.extend(
            [
                f'<line x1="{legend_x}" y1="{legend_y}" '
                f'x2="{legend_x + 24}" y2="{legend_y}" stroke="{color}" '
                f'stroke-width="2"{dash}/>',
                f'<text x="{legend_x + 30}" y="{legend_y + 4}" '
                f'font-family="sans-serif" font-size="11">{label}</text>',
            ]
        )

    svg.append("</svg>")
    SVG_PATH.write_text("\n".join(svg) + "\n", encoding="utf-8")


def main():
    rng = random.Random(SEED)
    results = [collect_result(load_factor, rng) for load_factor in LOAD_FACTORS]
    write_csv(results)
    write_svg(results)

    print(
        f"{'α':>8} {'n':>7} {'체이닝 성공':>14} {'선형 성공':>12} "
        f"{'체이닝 실패':>14} {'선형 실패':>12}"
    )
    for result in results:
        print(
            f"{result['load_factor']:8.3f} {result['entries']:7d} "
            f"{result['chaining_successful_average']:14.3f} "
            f"{result['linear_probing_successful_average']:12.3f} "
            f"{result['chaining_unsuccessful_average']:14.3f} "
            f"{result['linear_probing_unsuccessful_average']:12.3f}"
        )
    print(f"\nWrote {CSV_PATH.relative_to(REPOSITORY_ROOT)}")
    print(f"Wrote {SVG_PATH.relative_to(REPOSITORY_ROOT)}")


if __name__ == "__main__":
    main()
