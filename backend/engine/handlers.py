from engine.animations.animation_registry import ANIMATION_CLASSES

def handle_brightness(controller, data):
    value = data.get('value')
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
        print(f"Ignoring invalid brightness value: {value!r}")
        return
    controller.set_brightness(value)

def handle_clear(controller, data):
    controller.clear()

def handle_animation(controller, data):
    # animation_type matches the config path; name is accepted as a fallback
    # for older callers that used it to pick the class
    anim_type = data.get('animation_type') or data.get('name')
    anim_class = ANIMATION_CLASSES.get(anim_type)

    if not anim_class:
        print(f"Unknown animation requested: {anim_type}")
        return

    if 'color' in data:
        data['colors'] = [data.pop('color')]

    # Construct before touching the strip so bad parameters don't leave it
    # blanked with nothing playing
    try:
        animation = anim_class(**data)
    except Exception as e:
        print(f"Ignoring invalid animation '{anim_type}': {e}")
        return

    # Blank the strip before swapping so a shorter animation doesn't leave
    # the previous frame's tail lit; power on to match handle_config
    controller.clear()
    controller.set_power(True)
    controller.add_animation(animation)

def handle_config(controller, data):
    controller.clear()

    # Playing a scene implies turning on and unpausing — the frontend
    # already assumes this when it sets its power/play state
    controller.set_power(True)

    controller.config = data

    animations = data.get('animations', [])
    print(f"Loading scene '{data.get('name')}' ({len(animations)} animations)")

    for animation in animations:
        anim_name = animation.get('animation_type')
        anim_class = ANIMATION_CLASSES.get(anim_name)

        if not anim_class:
            print(f"Unknown animation in config: {anim_name}")
            continue

        if 'color' in animation:
            animation['colors'] = [animation.pop('color')]

        try:
            anim_instance = anim_class(**animation)
        except Exception as e:
            # One bad animation (e.g. a hand-edited saved scene with an
            # unknown field) shouldn't take down the rest of the scene
            print(f"Skipping animation '{animation.get('name')}': {e}")
            continue
        controller.add_animation(anim_instance)

def handle_get_status(controller):
    # Note: pixel data is deliberately excluded. At 1500 pixels the JSON
    # would approach the 32KB UDP read buffer in the API and risk truncation.
    current_state = {
        "active": controller.is_active(),
        "power": controller.is_power(),
        "brightness": controller.brightness,
        "num_pixels": controller.num_pixels,
        "animations": [type(anim).__name__ for anim in controller.animations]
    }
    return current_state

def handle_power(controller, data):
    state = data.get('value', 'off')
    if state == 'on':
        controller.set_power(True)
    else:
        controller.set_power(False)
        controller[:] = [(0, 0, 0) for _ in range(controller.num_pixels)]
        controller.show()

def handle_pause(controller, data):
    state = data.get('value', 'off')
    if state == 'off':
        controller.set_active(False)
    else:
        # Playing implies power on, matching handle_config; set_power(True)
        # also re-renders animations blanked by a prior power off
        controller.set_power(True)

COMMAND_HANDLERS = {
    "brightness": handle_brightness,
    "clear": handle_clear,
    "animation": handle_animation,
    "config": handle_config,
    "power": handle_power,
    "pause": handle_pause,
    "get_status": handle_get_status
}