"""Original vector space station: no external image downloads or fonts needed."""
import math
import pygame
from engine import COMMANDS
from ui import mix, panel, robot, text


DOCKS = (('ENERGIA', ('ricarica', 'attendi', 'controlla'), '#ffd078'),
         ('PORTELLO', ('apri', 'nega', 'accompagna', 'registra'), '#8bbfff'),
         ('MISSIONI', ('parti', 'soccorso', 'corsia_rapida', 'corsia_normale'), '#69e0c8'),
         ('RISORSE', ('carica', 'proteggi', 'allarme'), '#d1a3ff'))


def stars(surface, colors, tick=0):
    surface.fill(colors['bg'])
    width, height = surface.get_size()
    for i in range(85):
        x, y = (i * 173 + 53) % width, (i * i * 31 + 41) % height
        brightness = .16 + .16 * (1 + math.sin(tick * .4 + i)) / 2
        pygame.draw.circle(surface, mix(colors['bg'], colors['text'], brightness), (x, y), 1 if i % 8 else 2)


def station(surface, rect, colors, tick=0, actions=(), previous=(), progress=1, shake=0):
    panel(surface, rect, colors['panel'], colors['border'], 20)
    clip = surface.get_clip()
    surface.set_clip(rect.inflate(-4, -4).clip(clip))
    cx, cy = rect.centerx, rect.centery - 9
    sx, sy = rect.width / 660, rect.height / 244
    centers = [(cx - 225 * sx, cy - 57 * sy), (cx + 225 * sx, cy - 57 * sy),
               (cx + 225 * sx, cy + 63 * sy), (cx - 225 * sx, cy + 63 * sy)]
    for index, (name, commands, color) in enumerate(DOCKS):
        day = sum(colors['bg'][:3]) > 500
        color = pygame.Color((colors['accent'], colors['blue'], colors['mint'], '#774aab' if day else '#d1a3ff')[index])
        dx, dy = centers[index]
        active = bool(actions and actions[-1] in commands)
        linecolor = color if active else colors['border']
        pygame.draw.line(surface, linecolor, (cx, cy), (dx, dy), 4 if active else 2)
        for side in (-1, 1):
            solar = pygame.Rect(dx + side * 72 * sx - 13 * sx, dy - 23 * sy, 26 * sx, 46 * sy)
            panel(surface, solar, mix(colors['bg'], colors['blue'], .22), colors['border'], 3)
            for gridline in range(1, 4):
                yy = solar.y + solar.height * gridline / 4
                pygame.draw.line(surface, colors['border'], (solar.x, yy), (solar.right, yy))
        dock = pygame.Rect(0, 0, 125 * sx, 73 * sy)
        dock.center = dx, dy
        panel(surface, dock, mix(colors['card'], color, .12 if active else .02), color if active else colors['border'], 12)
        text(surface, name, (dx, dy - 20 * sy), 13, color, True, 'center')
        label = COMMANDS[actions[-1]] if active else 'IN ATTESA'
        text(surface, label, (dx, dy + 6 * sy), 13, colors['text'] if active else colors['muted'], anchor='center')
        if active:
            pygame.draw.circle(surface, color, (round(dx), round(dy + 25 * sy)), 3)
    pygame.draw.circle(surface, colors['bg'], (round(cx), round(cy)), round(68 * min(sx, sy)))
    pygame.draw.circle(surface, colors['border'], (round(cx), round(cy)), round(66 * min(sx, sy)), 2)
    for angle in range(0, 360, 45):
        a = math.radians(angle)
        pygame.draw.line(surface, colors['border'], (cx + math.cos(a) * 59 * sx, cy + math.sin(a) * 59 * sy),
                         (cx + math.cos(a) * 66 * sx, cy + math.sin(a) * 66 * sy), 2)
    def position(sequence):
        if not sequence:
            return cx, cy
        index = next((i for i, (_, commands, _) in enumerate(DOCKS) if sequence[-1] in commands), 0)
        dx, dy = centers[index]
        return cx + (dx - cx) * .55, cy + (dy - cy) * .55
    origin, target = position(previous), position(actions)
    t = max(0, min(1, progress))
    t = t * t * (3 - 2 * t)
    rx, ry = origin[0] + (target[0] - origin[0]) * t, origin[1] + (target[1] - origin[1]) * t
    robot(surface, (rx, ry + 4 * math.sin(tick * 1.7)), .73 * min(sx, sy), tick=tick, shake=shake)
    text(surface, 'STAZIONE ORBITALE · DRONE DI BORDO', (cx, rect.bottom - 16), 12, colors['muted'], anchor='center')
    surface.set_clip(clip)


def icon(size=256):
    result = pygame.Surface((size, size), pygame.SRCALPHA)
    center = (size // 2, size // 2)
    pygame.draw.circle(result, '#142438', center, size // 2 - 5)
    pygame.draw.circle(result, '#65dfc5', center, size // 2 - 15, max(3, size // 32))
    for angle in (-90, 30, 150):
        a = math.radians(angle)
        p = (center[0] + math.cos(a) * size * .3, center[1] + math.sin(a) * size * .3)
        pygame.draw.line(result, '#8bbfff', center, p, max(4, size // 24))
        pygame.draw.circle(result, '#ffd078', (round(p[0]), round(p[1])), size // 12)
    pygame.draw.circle(result, '#65dfc5', center, size // 9)
    return result


def flight_scene(surface, rect, colors, tick, gates, chosen=None, progress=0, shake=0, drone_id=1):
    """A visible fork: the selected hatch opens and the drone flies through it."""
    panel(surface, rect, colors['panel'], colors['border'], 22)
    clip = surface.get_clip()
    surface.set_clip(rect.inflate(-3, -3).clip(clip))
    center = (rect.x + 130, rect.centery)
    pygame.draw.circle(surface, mix(colors['panel'], colors['blue'], .14), (rect.x + 28, rect.bottom + 35), 133)
    pygame.draw.circle(surface, colors['border'], (rect.x + 28, rect.bottom + 35), 133, 2)
    for i in range(32):
        x = rect.x + (i * 73 + 19) % rect.width
        y = rect.y + (i * i * 29 + 13) % rect.height
        pygame.draw.circle(surface, colors['border'], (x, y), 1)
    text(surface, f'DRONE {drone_id:02}', (rect.x + 28, rect.y + 20), 15, colors['accent'], True)
    count = len(gates)
    no_action = chosen is not None and not gates[chosen]
    hold = chosen is not None and (no_action or gates[chosen][0] in ('attendi', 'nega'))
    gate_height = min(66, (rect.height - 32) / max(1, count) - 9)
    destinations = []
    for index in range(count):
        y = rect.y + 23 + (index + .5) * (rect.height - 46) / count
        end = (rect.right - 79, y)
        destinations.append(end)
        color = colors['mint'] if chosen == index else colors['border']
        pivot = (rect.x + rect.width * .47, center[1])
        pygame.draw.lines(surface, color, False, [center, pivot, (end[0] - 78, y), end], 3 if chosen == index else 1)
        gate = pygame.Rect(rect.right - 131, y - gate_height / 2, 104, gate_height)
        panel(surface, gate, colors['bg'], color, 9)
        opening = min(1, progress * 2.2) if chosen == index and not hold else 0
        half = round((gate.width - 8) / 2 * (1 - opening))
        if half:
            panel(surface, pygame.Rect(gate.x + 4, gate.y + 4, half, gate.height - 8), colors['card'], colors['border'], 4)
            panel(surface, pygame.Rect(gate.right - 4 - half, gate.y + 4, half, gate.height - 8), colors['card'], colors['border'], 4)
        text(surface, chr(65 + index), gate.center, 22, color if chosen == index else colors['text'], True, 'center')
        pygame.draw.circle(surface, color, (gate.right + 10, round(y)), 4)
    t = max(0, min(1, (progress - .12) / .88))
    ease = t * t * (3 - 2 * t)
    target = destinations[chosen] if chosen is not None and not hold else center
    x = center[0] + (target[0] - center[0]) * ease
    y = center[1] + (target[1] - center[1]) * ease
    if chosen is not None and not hold and 0 < t < 1:
        for index in range(4):
            pygame.draw.circle(surface, mix(colors['panel'], colors['accent'], .65 - index * .13), (round(x - 40 - index * 12), round(y + 7)), max(2, 7 - index))
    robot(surface, (x, y + (math.sin(tick * 2) * 4 if t == 0 else 0)), 1.13, tick=tick, shake=shake)
    if t >= 1:
        caption = 'NESSUNA AZIONE · IL DRONE RESTA QUI' if no_action else 'ORDINE ESEGUITO · IL DRONE NON PARTE' if hold else 'ORDINE ESEGUITO'
        text(surface, caption, (rect.x + 29, rect.bottom - 27), 14, colors['mint'], True)
    surface.set_clip(clip)
