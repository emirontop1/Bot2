local function random_name(i)
    return "f" .. tostring(i) .. "_"
end

return function(code)
    local replaced = {}
    local count = 0

    -- local değişkenleri yakala
    for name in code:gmatch("local%s+([%a_][%w_]*)") do
        if not replaced[name] then
            count = count + 1
            replaced[name] = random_name(count)
        end
    end

    -- aynı isimli değişkenleri değiştir
    for old, new in pairs(replaced) do
        code = code:gsub("([^%w_])" .. old .. "([^%w_])", "%1" .. new .. "%2")
    end

    -- local değişkenleri en üste taşı (çok basic)
    local locals = {}
    for name in pairs(replaced) do
        table.insert(locals, "local " .. replaced[name])
    end
    local header = table.concat(locals, "\n") .. "\n"

    return header .. "\n" .. code
end
