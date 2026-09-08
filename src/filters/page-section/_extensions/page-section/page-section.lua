
-- Format a page section
function Div(div)
  if div.classes:includes("page-section") then
    local has_bg_color = div.attributes['has_bg_color']
    local name = div.attributes['section_name']
    local content_class = div.attributes['content_class']

    local innerWrapper = pandoc.Div(div.content)
    innerWrapper.classes:extend({'page-section-content container'})

    if name then
      innerWrapper.classes:extend({'page-section-' .. name .. '__content'})
    end

    if content_class then
      innerWrapper.classes:extend({content_class})
    end

    if has_bg_color == 'primary' then
      innerWrapper.classes:extend({'text-white'})
    end

    local outerWrapper = pandoc.Div(innerWrapper)
    outerWrapper.classes:extend(div.classes)

    if name then
      outerWrapper.classes:extend({'page-section-' .. name})
    end

    if has_bg_color then
      outerWrapper.classes:extend({'page-section--has-' .. has_bg_color .. '-bg-color'})
    end

    return outerWrapper
  end
end
