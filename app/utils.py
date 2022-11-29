from app.printer import Printer


def format_time(value: float) -> str:
    days, rest = divmod(int(value), int(3600 * 24))
    hours, rest = divmod(rest, int(3600))
    minutes, seconds = divmod(rest, int(60))
    if days > 0:
        return f'{days} days {hours:02d}:{minutes:02d}:{seconds:02d}'
    elif hours > 0:
        return f'{hours:02d}:{minutes:02d}:{seconds:02d}'
    elif minutes > 0:
        return f'{minutes:02d}:{seconds:02d}'
    else:
        return f'{seconds}s'


def format_fillament_length(value: float) -> str:
    meters = value * 0.001
    return f'{meters:.1f}m'


def create_status_text(printer: Printer) -> str:
    data = printer.data
    state = data['print_stats']['state']

    text = (
        f'\N{White Heavy Check Mark} <i>state:</i> <b>{printer.state}</b>\n'
    )

    extruder_temperature = data['extruder']['temperature']
    extruder_target = data['extruder']['target']
    text += (
        f'\N{Thermometer} <i>extruder:</i> <b>{extruder_temperature:.2f}</b>\N{Degree Celsius} ({extruder_target:.2f}\N{Degree Celsius})\n'
    )

    bed_temperature = data['heater_bed']['temperature']
    bed_target = data['heater_bed']['target']
    text += (
        f'\N{Thermometer} <i>bed:</i> <b>{bed_temperature:.2f}</b>\N{Degree Celsius} ({bed_target:.2f}\N{Degree Celsius})\n'
    )

    if state in ('printing', 'complete'):
        filename = data['print_stats']['filename']
        filament_used = data['print_stats']['filament_used']
        print_duration = data['print_stats']['print_duration']
        progress = data['virtual_sdcard']['progress']

        estimated_print_duration = print_duration * (1 / progress - 1)

        text += (
            f'\N{Memo} <i>file:</i> <b>{filename}</b>\n'
            f'\N{Chequered Flag} <i>progress:</i> <b>{int(progress * 100)}%</b>\n'
            f'\N{Stopwatch} <i>print duration: </i> <b>{format_time(print_duration)}</b>\n'
            f'\N{Stopwatch} <i>estimated: </i> <b>{format_time(estimated_print_duration)}</b>\n'
            f'\N{Straight Ruler} <i>filament used: </i> <b>{format_fillament_length(filament_used)}</b>\n'
        )

    return text
