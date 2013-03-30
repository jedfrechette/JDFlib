--[[
Based on original lapse.lua script by Fraser McCrossan
Tested on SD780 IS.

An accurate intervalometer script, with locked focus and exposure, and screen
power off options.

Features:
 - accurate user defined frame interval
 - shoots continuously until stopped by user, out of power, or out of disk
   space.
 - can turn off the display before starting to shoot
 - use SET button to exit 

 See bottom of script for main loop.
]]

--[[
@title Locked Time-lapse
@param s Secs/frame
@default s 30
@param d Display Off
@default d 1
@range d 0 1
@param v Min Battery Voltage (mV)
@default v 2150
@range v 0 10000
--]]

-- convert parameters into readable variable names
secs_frame, display_off, min_vbatt = s, d, v

props = require "propcase"

-- derive actual running parameters from the more human-friendly input
-- parameters
function calculate_parameters (seconds_per_frame)
   local ticks_per_frame = 1000 * seconds_per_frame -- ticks per frame
   return ticks_per_frame
end

-- sleep, but using wait_click(); return true if a key was pressed, else false
function next_frame_sleep (frame, start_ticks, ticks_per_frame)
   -- this calculates the number of ticks between now and the time of
   -- the next frame
   local sleep_time = (start_ticks + frame * ticks_per_frame) - get_tick_count()
   if sleep_time < 1 then
      sleep_time = 1
   end
   wait_click(sleep_time)
   return not is_key("no_key")
end

-- delay for the appropriate amount of time, but respond to
-- the display key (allows turning off display to save power)
-- return true if we should exit, else false
function frame_delay (frame, start_ticks, ticks_per_frame)
   -- this returns true while a key has been pressed, and false if
   -- none
   while next_frame_sleep (frame, start_ticks, ticks_per_frame) do
      -- honour the display button (note this doesn't actually work)
      if is_key("display") then
	     click("display")
      end
      -- if set key is pressed, indicate that we should stop
      if is_key("set") then
	     return true
      end
   end
   return false
end

-- if the display mode is not the passed mode, click display and return true
-- otherwise return false
function seek_display_mode(mode)
   if get_prop(props.DISPLAY_MODE) == mode then
      return false
   else
      click "display"
      return true
   end
end

-- set and lock focus and exposure.
function lock_cam()
   local shooting = false
   local try = 1
   print "Press SET to exit"
   original_display_mode = get_prop(props.DISPLAY_MODE)
   if display_off then
      while seek_display_mode(2) do
         sleep(1000)
      end
   end
   while not shooting and try <= 5 do
      press("shoot_half")
      sleep(2000)
      shooting = get_shooting()
      if not shooting then
         release("shoot_half")
         sleep(2000)
         try = try + 1
      end
   end
   return shooting
end

if lock_cam() then
   start_ticks = get_tick_count()

   ticks_per_frame = calculate_parameters(secs_frame)

   frame = 1
   target_display_mode = 2 -- off

   abort = false
   repeat
      click("shoot_full_only")
      if frame_delay(frame, start_ticks, ticks_per_frame) then
         abort = true
      end
      if (get_vbatt() < min_vbatt ) then post_levent_to_ui('PressPowerButton') end
      if (get_jpg_count() < 1 ) then post_levent_to_ui('PressPowerButton') end
      frame = frame + 1
   until (abort)
   release("shoot_half")
else
   print("Unable to focus, quiting.")
end

-- restore display mode
if display_off then
   while seek_display_mode(original_display_mode) do
      sleep(1000)
   end
end

