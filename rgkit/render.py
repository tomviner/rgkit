import Tkinter
import time
import math

from rgkit import rg


def millis():
    return int(time.time() * 1000)


def rgb_to_hex(r, g, b, normalized=True):
    if normalized:
        return '#%02x%02x%02x' % (r*255, g*255, b*255)
    else:
        return '#%02x%02x%02x' % (r, g, b)


def blend_colors(color1, color2, weight):
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    r = r1 * weight + r2 * (1-weight)
    g = g1 * weight + g2 * (1-weight)
    b = b1 * weight + b2 * (1-weight)
    return (r, g, b)


class HighlightSprite:
    def __init__(self, loc, target, render):
        self.location = loc
        self.target = target
        self.renderer = render
        self.settings = self.renderer._settings
        self.hlt_square = None
        self.target_square = None

    def get_bot_color(self, loc):
        squareinfo = self.renderer.get_square_info(loc)
        # print squareinfo
        if 'bot' in squareinfo:
            bot = squareinfo[1]
            bot_color = RobotSprite.compute_color(self, bot['player'], bot['hp'])
            return bot_color
        return None

    def get_mixed_color(self, color, loc):
        bot_color = self.get_bot_color(loc)
        if bot_color is not None:
            color = blend_colors(color, bot_color, 0.7)
        return rgb_to_hex(*color)

    def clear(self):
        self.renderer.remove_object(self.hlt_square)
        self.renderer.remove_object(self.target_square)
        self.hlt_square = None
        self.target_square = None

    def animate(self, delta=0):
        if self.settings.highlight_cursor_blink:
            if not delta < self.settings.highlight_cursor_blink_interval:
                self.clear()
                return

        if self.location is not None:
            if self.hlt_square is None:
                color = self.settings.highlight_color
                color = self.get_mixed_color(color, self.location)
                self.hlt_square = self.renderer.draw_grid_object(self.location, fill=color, layer=3, width=0)
            if self.target is not None and self.target_square is None:
                color = self.settings.target_color
                color = self.get_mixed_color(color, self.target)
                self.target_square = self.renderer.draw_grid_object(self.target, fill=color, layer=3, width=0)


class RobotSprite:
    def __init__(self, action_info, render):
        self.location = action_info['loc']
        self.location_next = action_info['loc_end']
        self.action = action_info['name']
        self.target = action_info['target']
        self.hp = max(0, action_info['hp'])
        self.hp_next = max(0, action_info['hp_end'])
        self.id = action_info['player']
        self.renderer = render
        self.settings = self.renderer._settings
        self.animation_offset = (0, 0)

        # Tkinter objects
        self.square = None
        self.overlay = None
        self.text = None

    def animate(self, delta=0):
        """Animate this sprite

           delta is between 0 and 1. it tells us how far along to render (0.5 is halfway through animation)
                this allows animation logic to be separate from timing logic
        """
        # fix delta to between 0 and 1
        delta = max(0, min(delta, 1))
        bot_rgb_base = self.compute_color(self, self.id, self.hp)

        # default settings
        alpha_hack = 1
        bot_rgb = bot_rgb_base
        # if spawn, fade in
        if self.settings.bot_die_animation:
            if self.action == 'spawn':
                alpha_hack = delta
                bot_rgb = blend_colors(bot_rgb_base, self.settings.normal_color, delta)
            # if dying, fade out
            elif self.hp_next <= 0:
                alpha_hack = 1-delta
                bot_rgb = blend_colors(bot_rgb_base, self.settings.normal_color, 1-delta)

        x, y = self.location
        bot_size = self.renderer._blocksize
        self.animation_offset = (0, 0)
        arrow_fill = None

        # move animations
        if self.action == 'move' and self.target is not None:
            if self.renderer._animations and self.settings.bot_move_animation:
                # if normal move, start at bot location and move to next location
                # (note that first half of all move animations is the same)
                if delta < 0.5 or self.location_next == self.target:
                    x, y = self.location
                    tx, ty = self.target
                # if we're halfway through this animation AND the movement didn't succeed, reverse it (bounce back)
                else:
                    # starting where we wanted to go
                    x, y = self.target
                    # and ending where we are now
                    tx, ty = self.location
                dx = tx - x
                dy = ty - y
                off_x = dx*delta*self.renderer._blocksize
                off_y = dy*delta*self.renderer._blocksize
                self.animation_offset = (off_x, off_y)
            if self.settings.draw_movement_arrow:
                arrow_fill = 'lightblue'

        # attack animations
        elif self.action == 'attack' and self.target is not None:
            arrow_fill = 'orange'

        # guard animations
        elif self.action == 'guard':
            pass

        # suicide animations
        elif self.action == 'suicide':
            if self.renderer._animations and self.settings.bot_suicide_animation:
                # explosion animation (TODO size and color configurable in settings)
                # expand size (up to 1.5x original size)
                bot_size = self.renderer._blocksize * (1 + delta/2)
                # color fade to yellow
                bot_rgb = blend_colors(bot_rgb, (1, 1, 0), 1-delta)

        # DRAW ARROWS
        if arrow_fill is not None:
            if self.overlay is None and self.renderer.show_arrows.get():
                offset = (self.renderer._blocksize/2, self.renderer._blocksize/2)
                self.overlay = self.renderer.draw_line(self.location, self.target, layer=4, fill=arrow_fill, offset=offset, width=3.0, arrow=Tkinter.LAST)
            elif self.overlay is not None and not self.renderer.show_arrows.get():
                self.renderer.remove_object(self.overlay)
                self.overlay = None

        # DRAW BOTS WITH HP
        bot_hex = rgb_to_hex(*bot_rgb)
        self.draw_bot(delta, (x, y), bot_hex, bot_size)
        self.draw_bot_hp(delta if self.settings.bot_hp_animation else 0, (x, y), bot_rgb, alpha_hack)

    @staticmethod
    def compute_color(self, player, hp):
        r, g, b = self.settings.colors[player]
        maxclr = min(hp, 50)
        r += (100 - maxclr * 1.75) / 255
        g += (100 - maxclr * 1.75) / 255
        b += (100 - maxclr * 1.75) / 255
        return (r, g, b)

    def draw_bot(self, delta, loc, color, size):
        x, y, rx, ry = self.renderer.grid_bbox(loc, size-2)
        ox, oy = self.animation_offset
        if self.square is None:
            self.square = self.renderer.draw_grid_object(self.location, type=self.settings.bot_shape, layer=3, fill=color, width=0)
        self.renderer._win.itemconfig(self.square, fill=color)
        self.renderer._win.coords(self.square, (x+ox, y+oy, rx+ox, ry+oy))

    def draw_bot_hp(self, delta, loc, bot_color, alpha):
        x, y = self.renderer.grid_to_xy(loc)
        ox, oy = self.animation_offset
        tex_rgb = self.settings.text_color_bright \
            if self.hp_next > self.settings.robot_hp / 2 \
            else self.settings.text_color_dark
        tex_rgb = blend_colors(tex_rgb, bot_color, alpha)
        tex_hex = rgb_to_hex(*tex_rgb)
        val = int(self.hp * (1-delta) + self.hp_next * delta)
        if self.text is None:
            self.text = self.renderer.draw_text(self.location, val, tex_hex)
        self.renderer._win.itemconfig(self.text, text=val, fill=tex_hex)
        self.renderer._win.coords(
            self.text,
            (x+ox+(self.renderer._blocksize-self.renderer.cell_border_width)/2,
             y+oy+(self.renderer._blocksize-self.renderer.cell_border_width)/2))

    def clear(self):
        self.renderer.remove_object(self.square)
        self.renderer.remove_object(self.overlay)
        self.renderer.remove_object(self.text)
        self.square = None
        self.overlay = None
        self.text = None


class Render:
    def __init__(self, game_inst, settings, animations, names=["Red", "Blue"]):
        self.size_changed = False
        self.init = True

        self._settings = settings
        self._animations = animations
        self._blocksize = 25
        self._winsize = self._blocksize * self._settings.board_size + 40
        self._game = game_inst
        self._paused = True
        self._names = names
        self._layers = {}

        self.cell_border_width = 2

        self._master = Tkinter.Tk()
        self._master.configure(background="#333")
        self._master.title('Robot Game')

        width = self._winsize
        height = self._winsize

        self._board_frame = Tkinter.Frame(self._master, background="#555")
        self._info_frame = Tkinter.Frame(self._master, background="#333")
        self._control_frame = Tkinter.Frame(self._info_frame)

        self._board_frame.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, expand=True)

        #tkinter problem: 'pack' distributes space according to which widgets have
        # expand set to true, not to which directions they can actually expand to.
        self._info_frame.pack(side=Tkinter.BOTTOM)  # ,fill=Tkinter.X, expand=True)

        self._control_frame.pack(side=Tkinter.RIGHT)

        #tkinter problem: highlightthickness supposedly defaults to 0, but doesn't
        self._win = Tkinter.Canvas(
            self._board_frame, width=width, height=height,
            background="#555", highlightthickness=0)
        self._info = Tkinter.Canvas(
            self._info_frame, width=300, height=95,
            background="#333", highlightthickness=0)

        self._win.pack()
        self._info.pack(side=Tkinter.LEFT)

        self._master.bind('<Configure>', self.on_resize)

        self._labelred = self._info.create_text(
            self._blocksize / 2, self._blocksize * 1 / 4,
            anchor='nw', font='TkFixedFont', fill='red')
        self._labelblue = self._info.create_text(
            self._blocksize / 2, self._blocksize * 7 / 8,
            anchor='nw', font='TkFixedFont', fill='blue')
        self._label = self._info.create_text(
            self._blocksize / 2, self._blocksize * 3 / 2,
            anchor='nw', font='TkFixedFont', fill='white')
        self.create_controls(self._info, width, height)

        self._turn = 1.0
        self._sub_turn = 0.0

        self._highlighted = None
        self._highlighted_target = None

        # Animation stuff (also see #render heading in settings.py)
        self._sprites = []
        self._highlight_sprite = None
        self._t_paused = 0
        self._t_frame_start = 0
        self._t_next_frame = 0
        self._t_cursor_start = 0
        self._slider_delay = 0
        self.update_frame_start_time()

        self.draw_background()
        self.update_info_frame()
        self.update_sprites_new_turn()
        self.paint()

        self.callback()

        self._master.mainloop()

    def on_resize(self, event):
        self.size_changed = True

    def loc_robot_hp_color(self, loc):
        for index, color in enumerate(('red', 'blue')):
            self._game.get_actions_on_turn(self._turn)
            for robot in self._game.history[index][self._turn - 1]:
                if robot[0] == loc:
                    return (robot[1], index)
        return None

    def remove_object(self, obj):
        if obj is not None:
            self._win.delete(obj)

    def turn_changed(self):
        if self._settings.clear_highlight_between_turns:
            self._highlighted = None
        if self._settings.clear_highlight_target_between_turns:
            self._highlighted_target = None
        self.update_sprites_new_turn()
        self.update_info_frame()

    def update_block_size(self):
        if self.size_changed:
            if self.init:
                self.init = False
                return

            self.size_changed = False
            self._win.delete("all")
            # print "Size changed, adjusting cell size..."

            self._winsize = max(min(self._board_frame.winfo_width(), self._board_frame.winfo_height()), 250)
            self._blocksize = (self._winsize-40)/self._settings.board_size
            self._win.configure(width=self._winsize, height=self._winsize)

            self.draw_background()
            self.update_sprites_new_turn()
            self.paint()

    def step_turn(self, turns):
        self._turn = self.current_turn_int() + turns
        self._turn = min(max(self._turn, 1.0), self._game.state.turn)
        self._sub_turn = 0.0
        self.update_frame_start_time()
        self.turn_changed()
        self.update_info_frame()
        self.paint()

    def toggle_pause(self):
        self._paused = not self._paused
        # print "paused" if self._paused else "unpaused"
        self._toggle_button.config(text=u'\u25B6' if self._paused else u'\u25FC')
        now = millis()
        if self._paused:
            self._t_paused = now
            self._sub_turn = 0.0
        else:
            self.update_frame_start_time(now)

    def update_frame_start_time(self, tstart=None):
        tstart = tstart or millis()
        self._t_frame_start = tstart

        self._t_next_frame = tstart + self._slider_delay

    def create_controls(self, win, width, height):
        def step_turn(turns):
            if not self._paused:
                self.toggle_pause()
            self.step_turn(turns)

        def prev():
            step_turn(-1)

        def next():
            step_turn(+1)

        def restart():
            step_turn((-self._turn)+1)

        def pause():
            self.toggle_pause()
            self.update_info_frame()

        def onclick(event):
            x = (event.x - 20) / self._blocksize
            y = (event.y - 20) / self._blocksize
            loc = (x, y)
            if loc[0] >= 0 and loc[1] >= 0 and loc[0] < self._settings.board_size and loc[1] < self._settings.board_size:
                if loc == self._highlighted:
                    self._highlighted = None
                else:
                    self._highlighted = loc
                action = self._game.get_actions_on_turn(self.current_turn_int()).get(loc)
                if action is not None:
                    self._highlighted_target = action.get("target", None)
                else:
                    self._highlighted_target = None
                self.update_highlight_sprite()
                self.update_info_frame()
                self._t_cursor_start = millis()

        self._master.bind("<Button-1>", lambda e: onclick(e))
        self._master.bind('<Left>', lambda e: prev())
        self._master.bind('<Right>', lambda e: next())
        self._master.bind('<space>', lambda e: pause())

        self.show_arrows = Tkinter.BooleanVar()

        frame = self._control_frame

        arrows_box = Tkinter.Checkbutton(frame, text="Show Arrows", variable=self.show_arrows, command=self.paint)
        arrows_box.pack()

        self._toggle_button = Tkinter.Button(frame, text=u'\u25B6', command=pause)
        self._toggle_button.pack(side='left')

        prev_button = Tkinter.Button(frame, text='<', command=prev)
        prev_button.pack(side='left')

        next_button = Tkinter.Button(frame, text='>', command=next)
        next_button.pack(side='left')

        restart_button = Tkinter.Button(frame, text='<<', command=restart)
        restart_button.pack(side='left')

        self._time_slider = Tkinter.Scale(frame,
                                          from_=-self._settings.turn_interval/2,
                                          to_=self._settings.turn_interval/2,
                                          orient=Tkinter.HORIZONTAL, borderwidth=0,
                                          length=90)
        self._time_slider.pack(fill=Tkinter.X)
        self._time_slider.set(0)

    def draw_grid_object(self, loc, type="square", layer=0, **kargs):
        layer_id = 'layer %d' % layer
        self._layers[layer_id] = None
        tags = kargs.get("tags", [])
        tags.append(layer_id)
        kargs["tags"] = tags
        x, y = self.grid_to_xy(loc)
        rx, ry = self.square_bottom_corner((x, y))
        if type == "square" or self._settings.bot_shape == "square":
            item = self._win.create_rectangle(
                x, y, rx, ry,
                **kargs)
        elif type == "circle":
            item = self._win.create_oval(
                x, y, rx, ry,
                **kargs)
        return item

    def update_layers(self):
        for layer in self._layers:
            self._win.tag_raise(layer)

    def draw_text(self, loc, text, color=None):
        layer_id = 'layer %d' % 9
        self._layers[layer_id] = None
        x, y = self.grid_to_xy(loc)
        item = self._win.create_text(
            x+(self._blocksize-self.cell_border_width)/2,
            y+(self._blocksize-self.cell_border_width)/2,
            text=text, font='TkFixedFont', fill=color, tags=[layer_id])
        return item

    def draw_line(self, src, dst, offset=(0, 0), layer=0, **kargs):
        layer_id = 'layer %d' % layer
        self._layers[layer_id] = None
        tags = kargs.get("tags", [])
        tags.append(layer_id)
        kargs["tags"] = tags
        ox, oy = offset
        srcx, srcy = self.grid_to_xy(src)
        dstx, dsty = self.grid_to_xy(dst)

        item = self._win.create_line(srcx+ox, srcy+oy, dstx+ox, dsty+oy, **kargs)
        return item

    def update_info_frame(self):
        display_turn = self.current_turn_int()
        max_turns = self._settings.max_turns
        count_turn = int(math.ceil(self._turn + self._sub_turn))
        if count_turn > self._settings.max_turns:
            count_turn = self._settings.max_turns
        if count_turn < 0:
            count_turn = 0
        red = len(self._game.history[0][count_turn-1])
        blue = len(self._game.history[1][count_turn-1])
        info = ''
        currentAction = ''
        if self._highlighted is not None:
            squareinfo = self.get_square_info(self._highlighted)
            if 'obstacle' in squareinfo:
                info = 'Obstacle'
            elif 'bot' in squareinfo:
                actioninfo = squareinfo[1]
                hp = actioninfo['hp']
                team = actioninfo['player']
                info = '%s Bot: %d HP' % (['Red', 'Blue'][team], hp)
                if actioninfo.get('name') is not None:
                    currentAction += 'Current Action: %s' % (actioninfo['name'],)
                    if self._highlighted_target is not None:
                        currentAction += ' to %s' % (self._highlighted_target,)

        r_text = '%s: %d' % (self._names[0], red)
        g_text = '%s: %d' % (self._names[1], blue)
        white_text = [
            'Turn: %d/%d' % (display_turn, max_turns),
            'Highlighted: %s; %s' % (self._highlighted, info),
            currentAction
        ]
        self._info.itemconfig(self._label, text='\n'.join(white_text))
        self._info.itemconfig(self._labelred, text=r_text)
        self._info.itemconfig(self._labelblue, text=g_text)

    def current_turn_int(self):
        return min(int(math.floor(self._turn + self._sub_turn)), self._settings.max_turns)

    def get_square_info(self, loc):
        if loc in self._settings.obstacles:
            return ['obstacle']

        all_bots = self._game.get_actions_on_turn(self.current_turn_int())
        if loc in all_bots:
            return ['bot', all_bots[loc]]

        return ['normal']

    def update_slider_value(self):
        v = -self._time_slider.get()
        if v > 0:
            v = v * 20
        self._slider_delay = self._settings.turn_interval + v

    def callback(self):
        self.update_slider_value()
        self.tick()
        self._win.after(int(1000.0 / self._settings.FPS), self.callback)

    def tick(self):
        now = millis()

        # check if frame-update
        if self._animations:
            if not self._paused:
                self._sub_turn = max(0.0, float((now - self._t_frame_start)) / float(self._slider_delay))
                if self._turn >= self._settings.max_turns:
                    self.toggle_pause()
                    self._turn = self._settings.max_turns
                self.update_info_frame()
                if self._sub_turn >= 1:
                    self._sub_turn -= 1
                    self._turn += 1
                    self.update_frame_start_time(self._t_next_frame)
                    self.turn_changed()
            subframe_hlt = float((now - self._t_cursor_start) % self._settings.rate_cursor_blink) / float(self._settings.rate_cursor_blink)
            self.paint(self._sub_turn, subframe_hlt)
        elif now > self._t_next_frame and not self._paused:
            self._turn += 1
            self.update_frame_start_time(self._t_next_frame)
            self.turn_changed()
            self.paint(0, 0)

        self.update_block_size()

    def determine_bg_color(self, loc):
        if loc in self._settings.obstacles:
            return rgb_to_hex(*self._settings.obstacle_color)
        return rgb_to_hex(*self._settings.normal_color)

    def draw_background(self):
        # draw squares
        for y in range(self._settings.board_size):
            for x in range(self._settings.board_size):
                loc = (x, y)
                self.draw_grid_object(loc, fill=self.determine_bg_color(loc), layer=1, width=0)
        # draw text labels
        text_color = rgb_to_hex(*self._settings.text_color)
        for y in range(self._settings.board_size):
            self.draw_text((y, 0), str(y), color=text_color)
            self.draw_text((0, y), str(y), color=text_color)

    def update_sprites_new_turn(self):
        for sprite in self._sprites:
            sprite.clear()
        self._sprites = []

        self.update_highlight_sprite()
        turn_action = self.current_turn_int()
        bots_activity = self._game.get_actions_on_turn(turn_action)
        try:
            for bot_data in bots_activity.values():
                self._sprites.append(RobotSprite(bot_data, self))
        except:
            print "PROBLEM UPDATING SPRITES..? bots at turn %d:" % turn_action, bots_activity

    def update_highlight_sprite(self):
        need_update = self._highlight_sprite is not None and self._highlight_sprite.location != self._highlighted
        if self._highlight_sprite is not None or need_update:
            self._highlight_sprite.clear()
        self._highlight_sprite = HighlightSprite(self._highlighted, self._highlighted_target, self)
        self.paint_highlight_sprite(0)

    def paint_highlight_sprite(self, subframe_hlt=0):
        if self._highlight_sprite is not None:
            self._highlight_sprite.animate(subframe_hlt)

    def paint(self, subframe=0, subframe_hlt=0):
        for sprite in self._sprites:
            sprite.animate(subframe)
        self.update_highlight_sprite()
        self.paint_highlight_sprite(subframe_hlt)
        self.update_layers()

    def grid_to_xy(self, loc):
        x, y = loc
        return (x * self._blocksize + 20, y * self._blocksize + 20)

    def square_bottom_corner(self, square_topleft):
        x, y = square_topleft
        return (x + self._blocksize - self.cell_border_width, y + self._blocksize - self.cell_border_width)

    def grid_bbox(self, loc, width=25):
        x, y = self.grid_to_xy(loc)
        x += (self._blocksize - self.cell_border_width) / 2.
        y += (self._blocksize - self.cell_border_width) / 2.
        halfwidth = self._blocksize / 2.
        halfborder = self.cell_border_width / 2.
        return (int(x-halfwidth+halfborder), int(y-halfwidth+halfborder), int(x+halfwidth-halfborder), int(y+halfwidth-halfborder))
