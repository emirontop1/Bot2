-- main.lua
local ok_socket, socket = pcall(require, "socket")
local ok_dkjson, json = pcall(require, "dkjson")

if not ok_socket then
    io.stderr:write("Missing module 'socket'. Please install 'luasocket' via luarocks.\n")
    -- exit with non-zero so Docker/Cmd wrapper gösterir
    os.exit(1)
end

if not ok_dkjson then
    io.stderr:write("Missing module 'dkjson'. Please install 'dkjson' via luarocks.\n")
    os.exit(1)
end

local port = tonumber(os.getenv("PORT")) or 8080
local server = assert(socket.bind("*", port))
server:settimeout(0.01)
print("Listening on port " .. port)

while true do
    local client = server:accept()
    if client then
        -- Basit health route for testing
        local line = client:receive("*l")
        if line then
            local method, path = line:match("^(%S+)%s+(%S+)")
            if method == "GET" and path == "/" then
                client:send("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 16\r\n\r\nServer is running\n")
            else
                client:send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n" .. json.encode({status="ok", path=path}) )
            end
        end
        client:close()
    else
        socket.sleep(0.01)
    end
end
