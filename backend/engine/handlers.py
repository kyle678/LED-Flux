from engine.animations.animation_registry import ANIMATION_CLASSES

def handle_brightness(controller, data):
    value = data.get('value', 0) 
    controller.set_brightness(value)

def handle_clear(controller, data):
    controller.clear()

def handle_animation(controller, data):
    anim_name = data.get('name')
    anim_class = ANIMATION_CLASSES.get(anim_name)
    
    if not anim_class:
        print(f"Unknown animation requested: {anim_name}")
        return
    
    controller.animations = []
    animation = anim_class(**data)
    controller.add_animation(animation)

def handle_config(controller, data):
    controller.clear()
    
    controller.config = data

    print(data)
    
    for animation in data.get('animations', []):
        anim_name = animation.get('animation_type')
        anim_class = ANIMATION_CLASSES.get(anim_name)
        print(f"Configuring animation: {anim_name}")
        print(f"Animation parameters: {animation}")
        
        if not anim_class:
            print(f"Unknown animation in config: {anim_name}")
            continue

        if 'color' in animation:
            animation['colors'] = [animation.pop('color')]
        
        anim_instance = anim_class(**animation)
        controller.add_animation(anim_instance)

def handle_get_status(controller):
    current_state = {
        "active": controller.is_active(),
        "power": controller.is_power(),
        "brightness": controller.brightness,
        "num_pixels": controller.num_pixels,
        "animations": [type(anim).__name__ for anim in controller.animations],
        "pixels": controller[:]
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
        controller.set_active(True)

COMMAND_HANDLERS = {
    "brightness": handle_brightness,
    "clear": handle_clear,
    "animation": handle_animation,
    "config": handle_config,
    "power": handle_power,
    "pause": handle_pause,
    "config": handle_config,
    "get_status": handle_get_status
}