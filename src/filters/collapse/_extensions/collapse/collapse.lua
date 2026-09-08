-- Collapse a div
function Div(div)
  if div.classes:includes("collapse") then
    local id = tostring({}):sub(10)
    local title = div.attributes['title']

    div.attributes['collapse'] = nil -- consume attribute

    local button = pandoc.RawInline(
      'html',
      '<button \
        class="collapse-button collapsed" \
        type="button" \
        data-bs-toggle="collapse" \
        data-bs-target="#' .. id .. '" \
        aria-expanded="false" \
        aria-controls="' .. id .. '">'
          .. title ..
      '</button>'
    )
     
    local content = pandoc.Div(div.content)
    content.attributes['id'] = id
    content.classes:extend({'collapse collapse-content'})

    local wrapper = pandoc.Div({button, content})
    wrapper.classes:extend({'collapse-wrapper'})

    return wrapper
  end
end
