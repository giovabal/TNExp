from collections.abc import Iterable

from webapp.utils.colors import hex_to_rgb, rgb_avg

import pypalettes

DEFAULT_FALLBACK_COLOR = (204, 204, 204)


def parse_color(value):
    if hasattr(value, "hex"):
        return parse_color(value.hex)
    if hasattr(value, "hex_code"):
        return parse_color(value.hex_code)
    if hasattr(value, "rgb"):
        return parse_color(value.rgb)
    if hasattr(value, "rgba"):
        return parse_color(value.rgba)

    if isinstance(value, dict):
        rgb_keys = (("r", "g", "b"), ("red", "green", "blue"))
        for keys in rgb_keys:
            if all(key in value for key in keys):
                return parse_color([value[key] for key in keys])

    if isinstance(value, (list, tuple)):
        values = [float(part) for part in value[:3]]
        if values and max(values) <= 1:
            return tuple(int(part * 255) for part in values)
        return tuple(int(part) for part in values)

    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned.lower().startswith("rgb"):
            channel_values = cleaned[cleaned.find("(") + 1 : cleaned.rfind(")")].split(",")
            parsed = [float(part.strip()) for part in channel_values if part.strip()]
            if not parsed:
                return DEFAULT_FALLBACK_COLOR
            if max(parsed) <= 1:
                return tuple(int(part * 255) for part in parsed[:3])
            return tuple(int(part) for part in parsed[:3])

        if "," in cleaned:
            parts = [part.strip() for part in cleaned.split(",") if part.strip()]
            parsed = [float(part) for part in parts[:3]]
            if not parsed:
                return DEFAULT_FALLBACK_COLOR
            if max(parsed) <= 1:
                return tuple(int(part * 255) for part in parsed[:3])
            return tuple(int(part) for part in parsed[:3])

        if " " in cleaned:
            parts = [part for part in cleaned.split(" ") if part]
            if len(parts) >= 3 and all(part.replace(".", "", 1).isdigit() for part in parts[:3]):
                parsed = [float(part) for part in parts[:3]]
                if max(parsed) <= 1:
                    return tuple(int(part * 255) for part in parsed[:3])
                return tuple(int(part) for part in parsed[:3])

        if cleaned.lower().startswith("0x"):
            cleaned = cleaned[2:]
        if cleaned.startswith("#"):
            cleaned = cleaned[1:]

        if len(cleaned) in {8, 4} and all(char in "0123456789abcdefABCDEF" for char in cleaned):
            cleaned = cleaned[:-2] if len(cleaned) == 8 else cleaned[:-1]

        try:
            return hex_to_rgb(cleaned)
        except ValueError:
            return DEFAULT_FALLBACK_COLOR

    if isinstance(value, Iterable):
        try:
            return parse_color(list(value))
        except TypeError:
            return DEFAULT_FALLBACK_COLOR

    return DEFAULT_FALLBACK_COLOR


def palette_colors(name):
    if hasattr(pypalettes, "load_palette"):
        palette = pypalettes.load_palette(name)
    elif hasattr(pypalettes, "get_palette"):
        palette = pypalettes.get_palette(name)
    elif hasattr(pypalettes, "Palette"):
        palette = pypalettes.Palette(name)
    else:
        palette = None

    if palette is None:
        raise ValueError(f"Palette '{name}' could not be loaded.")

    colors = None
    for attr in ("colors", "hex_colors", "palette", "hex"):
        if not hasattr(palette, attr):
            continue
        candidate = getattr(palette, attr)
        if callable(candidate):
            try:
                candidate = candidate()
            except TypeError:
                continue

        if isinstance(candidate, str):
            if attr == "hex":
                continue
            candidate = [candidate]

        try:
            candidate_list = list(candidate)
        except TypeError:
            continue

        if candidate_list:
            colors = candidate_list
            break

    if colors is None:
        if isinstance(palette, str):
            colors = [palette]
        else:
            try:
                colors = list(palette)
            except TypeError as error:
                raise ValueError(f"Palette '{name}' has no iterable colors.") from error

    return colors


def expand_colors(colors, count):
    if not colors:
        return []
    if len(colors) >= count:
        return list(colors[:count])
    repeats = (count + len(colors) - 1) // len(colors)
    return (list(colors) * repeats)[:count]


def colors_for_groups(group_keys, palette_name):
    palette_values = palette_colors(palette_name)
    palette_values = expand_colors(palette_values, len(group_keys))
    return {
        group_key: rgb_to_csv(parse_color(palette_color))
        for group_key, palette_color in zip(group_keys, palette_values, strict=False)
    }


def average_color(colors):
    if not colors:
        return DEFAULT_FALLBACK_COLOR
    totals = [0, 0, 0]
    for color in colors:
        for index, value in enumerate(parse_color(color)):
            totals[index] += value
    count = len(colors)
    return tuple(int(total / count) for total in totals)


def rgb_to_csv(color):
    return ",".join(str(value) for value in parse_color(color))


def muted_edge_color(source_color, target_color, factor=0.75):
    color = rgb_avg(parse_color(source_color), parse_color(target_color))
    return ",".join(str(int(channel * factor)) for channel in color)
