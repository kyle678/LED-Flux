import math

class Colors:

    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    YELLOW = (255, 255, 0)
    GREEN = (0, 255, 0)
    CYAN = (0, 255, 255)
    BLUE = (0, 0, 255)
    MAGENTA = (255, 0, 255)

    @staticmethod
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

class Utils:
    @staticmethod
    def getGradient(length, c1, c2):
        # Prevent ZeroDivisionError and handle edge cases
        if length <= 0:
            return []
        if length == 1:
            return [tuple(c1)]

        colors = []
        for i in range(length):
            f1 = i / (length - 1)
            f2 = 1 - f1
            color = [int((c1[x] * f2) + (c2[x] * f1)) for x in range(3)]
            colors.append(tuple(color))
        return colors

    @staticmethod
    def getMultiGradient(length, colors, wrap=False):
        if not colors:
            return []
        if len(colors) == 1:
            return [tuple(colors[0])] * length

        gradient_colors = []
        num_colors = len(colors)
        count = num_colors - 1

        if wrap: 
            count += 1

        for i in range(count):
            c1 = colors[i]
            c2 = colors[(i + 1) % num_colors]
            
            # Use proportional fractions to calculate precise start and end indices.
            # This perfectly absorbs remainder pixels without exceeding the total length.
            start_idx = int((i / count) * length)
            end_idx = int(((i + 1) / count) * length)
            segment_length = end_idx - start_idx
            
            gradient_colors.extend(Utils.getGradient(segment_length, c1, c2))
            
        return gradient_colors

    @staticmethod
    def getAlternatingColors(length, colors, step):
        if not colors:
            return []
        if len(colors) == 1:
            return [tuple(colors[0])] * length

        alternating_colors = []
        num_colors = len(colors)

        for i in range(length):
            color_index = (i // step) % num_colors
            alternating_colors.append(tuple(colors[color_index]))

        return alternating_colors

    @staticmethod
    def generateColorArray(length, colors, gradient=True, wrap=False, step=1):
        if gradient:
            return Utils.getMultiGradient(length, colors, wrap)
        else:
            return Utils.getAlternatingColors(length, colors, step)

    @staticmethod
    def rotate(pixels, n):
        n = n % len(pixels)
        pixels[:] = pixels[-n:] + pixels[:-n]

    @staticmethod
    def rotate_copy(pixels, n):
        n = n % len(pixels)
        return pixels[-n:] + pixels[:-n]