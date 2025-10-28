local http = require("socket.http")
local ltn12 = require("ltn12")
local json = require("dkjson")
local obfuscate = require("./obfuscator")

local server = require("socket").bind("*", 8080)
print("Lua Obfuscator API running on port 8080")

while true do
    local client = server:accept()
    client:settimeout(10)
    local line, err = client:receive("*l")

    if not line then
        client:close()
    else
        local method, path = line:match("^(%S+)%s+(%S+)")
        local headers = {}
        repeat
            local h = client:receive("*l")
            if h and h ~= "" then
                local k, v = h:match("^(.-):%s*(.*)")
                if k and v then headers[k:lower()] = v end
            end
        until not h or h == ""

        local body = ""
        if headers["content-length"] then
            body = client:receive(tonumber(headers["content-length"]))
        end

        local data = json.decode(body)
        local result = obfuscate(data.code or "")

        local response = json.encode({ obfuscated = result })
        client:send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n" .. response)
        client:close()
    end
end
