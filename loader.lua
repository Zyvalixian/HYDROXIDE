local hxd_env = getgenv()
hxd_env.HXD_LOAD_MODE = "remote"
hxd_env.HXD_REMOTE_ROOT = "https://raw.githubusercontent.com/Viatanyl/HYDROXIDE/refs/heads/main/"
hxd_env.HXD_LOCAL_ROOT = hxd_env.HXD_LOCAL_ROOT or "HYDROXIDE_REPO/"

local gameId = game.GameId
if gameId == 1087859240 then
    pcall(function()
        loadstring(game:HttpGet(
            hxd_env.HXD_REMOTE_ROOT .. "ROGUE/rogue_ui.lua",
            true
        ))()
    end)
elseif gameId == 7359098240 then
    pcall(function()
        loadstring(game:HttpGet(
            "https://raw.githubusercontent.com/heisenburgah/HYDROXIDE/main/ROGUE_BATTLEGROUNDS/rlb.lua",
            true
        ))()
    end)
end
