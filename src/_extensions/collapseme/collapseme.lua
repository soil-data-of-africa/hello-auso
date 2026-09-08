return {
    ['collapseme'] = function(args, kwargs, meta)
      local e = tostring({}):sub(10)
      local ttl = pandoc.utils.stringify(kwargs['ttl'])
      local txt = pandoc.utils.stringify(kwargs['txt'])
      local link = pandoc.utils.stringify(kwargs['link'])
      local cit  = pandoc.utils.stringify(kwargs['cit'])
      local f1 = '<div class="accordion-item"><h2 class="accordion-header"><button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#' .. e .. '" aria-expanded="false" aria-controls="' .. e .. '">'
      local f2 = '</button></h2><div id="' .. e .. '" class="accordion-collapse collapse"><div class="accordion-body"><p>'
      local f3 = '</p><p>Citation: <i>'
      local f4 = '</i></p><ul class="list-unstyled mb-0 mt-3"><li><a class="fw-semibold" href="' .. link .. '" target="_blank"><i class="bi-download me-2"></i>Read more</a></li></ul></div></div></div>'
      local res = f1 .. ttl .. f2 .. txt .. f3 .. cit .. f4
      return pandoc.RawBlock('html',res)
    end
}

