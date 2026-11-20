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


CAPACITY = 4093
SEED = 20261120
TOKEN_CHARACTERS = string.ascii_letters + string.digits
CSV_PATH = REPOSITORY_ROOT / "experiments" / "results.csv"
SVG_PATH = REPOSITORY_ROOT / "experiments" / "results.svg"


def random_url(rng):
    host = "".join(rng.choices(TOKEN_CHARACTERS, k=16))
    path = "".join(rng.choices(TOKEN_CHARACTERS, k=24))
    return f"https://{host}.example/{path}"


def collect_result(target_load, rng):
    entry_count = round(CAPACITY * target_load)
    table = HashTable(capacity=CAPACITY, max_load=None)
    inserted_urls = []

    while len(inserted_urls) < entry_count:
        url = random_url(rng)
        if table.get(url) is None:
            table.set(url, len(inserted_urls))
            inserted_urls.append(url)

    successful_comparisons = 0
    for url in inserted_urls:
        _, comparisons = table.get_with_comparisons(url)
        successful_comparisons += comparisons

    unsuccessful_comparisons = 0
    for _ in inserted_urls:
        url = random_url(rng)
        while table.get(url) is not None:
            url = random_url(rng)
        _, comparisons = table.get_with_comparisons(url)
        unsuccessful_comparisons += comparisons

    load_factor = len(table) / table.capacity
    return {
        "load_factor": load_factor,
        "entries": len(table),
        "successful_average": successful_comparisons / len(inserted_urls),
        "successful_theory": 1 + load_factor / 2,
        "unsuccessful_average": unsuccessful_comparisons / len(inserted_urls),
        "unsuccessful_theory": load_factor,
    }


def write_csv(results):
    fieldnames = (
        "load_factor",
        "entries",
        "successful_average_comparisons",
        "successful_theory",
        "unsuccessful_average_comparisons",
        "unsuccessful_theory",
    )
    with CSV_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(
            output_file, fieldnames=fieldnames, lineterminator="\n"
        )
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "load_factor": f"{result['load_factor']:.6f}",
                    "entries": result["entries"],
                    "successful_average_comparisons": (
                        f"{result['successful_average']:.6f}"
                    ),
                    "successful_theory": f"{result['successful_theory']:.6f}",
                    "unsuccessful_average_comparisons": (
                        f"{result['unsuccessful_average']:.6f}"
                    ),
                    "unsuccessful_theory": (
                        f"{result['unsuccessful_theory']:.6f}"
                    ),
                }
            )


def write_svg(results):
    width, height = 960, 560
    left, right, top, bottom = 82, 30, 96, 72
    chart_width = width - left - right
    chart_height = height - top - bottom
    x_min = results[0]["load_factor"]
    x_max = results[-1]["load_factor"]
    y_max = math.ceil(
        max(
            result[key]
            for result in results
            for key in (
                "successful_average",
                "successful_theory",
                "unsuccessful_average",
                "unsuccessful_theory",
            )
        )
    )

    def x_position(load_factor):
        return left + (load_factor - x_min) / (x_max - x_min) * chart_width

    def y_position(value):
        return top + chart_height - value / y_max * chart_height

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        "<title>Hash-table probe counts vs. load factor</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="480" y="30" text-anchor="middle" font-family="sans-serif" '
        'font-size="20">Average node comparisons vs. load factor</text>',
    ]

    for tick in range(y_max + 1):
        y = y_position(tick)
        svg.extend(
            [
                f'<line x1="{left}" y1="{y:.2f}" x2="{width - right}" '
                f'y2="{y:.2f}" stroke="#dddddd"/>',
                f'<text x="{left - 12}" y="{y + 5:.2f}" text-anchor="end" '
                f'font-family="sans-serif" font-size="12">{tick}</text>',
            ]
        )

    x_ticks = sorted({round(x_min, 2), 1.0, 2.0, 3.0, round(x_max, 2)})
    for tick in x_ticks:
        x = x_position(tick)
        svg.extend(
            [
                f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" '
                f'y2="{top + chart_height}" stroke="#eeeeee"/>',
                f'<text x="{x:.2f}" y="{top + chart_height + 22}" '
                f'text-anchor="middle" font-family="sans-serif" '
                f'font-size="12">{tick:g}</text>',
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
            "Average node comparisons</text>",
        ]
    )

    series = (
        ("successful_average", "#1769aa", "Successful (measured)", True),
        ("successful_theory", "#1769aa", "Successful (theory: 1 + α/2)", False),
        ("unsuccessful_average", "#d1495b", "Unsuccessful (measured)", True),
        ("unsuccessful_theory", "#d1495b", "Unsuccessful (theory: α)", False),
    )
    legend_positions = ((170, 52), (550, 52), (170, 78), (550, 78))
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
    results = [collect_result(step / 4, rng) for step in range(1, 17)]
    write_csv(results)
    write_svg(results)

    print(
        f"{'α':>8} {'n':>7} {'성공 평균':>12} {'성공 이론':>12} "
        f"{'실패 평균':>12} {'실패 이론':>12}"
    )
    for result in results:
        print(
            f"{result['load_factor']:8.3f} {result['entries']:7d} "
            f"{result['successful_average']:12.3f} "
            f"{result['successful_theory']:12.3f} "
            f"{result['unsuccessful_average']:12.3f} "
            f"{result['unsuccessful_theory']:12.3f}"
        )
    print(f"\nWrote {CSV_PATH.relative_to(REPOSITORY_ROOT)}")
    print(f"Wrote {SVG_PATH.relative_to(REPOSITORY_ROOT)}")


if __name__ == "__main__":
    main()
