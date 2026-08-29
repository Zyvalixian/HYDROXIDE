local hxd_env = getgenv()
hxd_env.HXD_LOAD_MODE = "local"
hxd_env.HXD_LOCAL_ROOT = "HYDROXIDE_REPO/"
hxd_env.HXD_REMOTE_ROOT = "https://raw.githubusercontent.com/Viatanyl/HYDROXIDE/refs/heads/main/"

local path = hxd_env.HXD_LOCAL_ROOT .. "ROGUE/rogue_ui.lua"
local fn, err

if isfile and not isfile(path) then
    warn("Local script missing: " .. path)
    return
end

if loadfile then
    fn, err = loadfile(path)
elseif readfile then
    local code = readfile(path)
    fn, err = loadstring(code)
else
    warn("No local file loader available")
    return
end

if not fn then
    warn(err)
    return
end

fn()
