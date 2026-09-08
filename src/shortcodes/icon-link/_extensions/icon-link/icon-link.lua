return {
  ['icon-link'] = function(args, kwargs, meta) 
    local icon = 'bi-' .. pandoc.utils.stringify(kwargs['icon'])
    local link = pandoc.utils.stringify(kwargs['link'])
    local title = pandoc.utils.stringify(kwargs['title'])

    local iconLink = pandoc.RawInline(
      'html',
      '<a \
        class="fw-semibold" \
        href="' .. link .. '" \
        target="_blank"\
      >\
        <i class="' .. icon .. ' me-2"></i>\
        ' .. title .. '\
      </a>'
    )

    return iconLink
  end
}
