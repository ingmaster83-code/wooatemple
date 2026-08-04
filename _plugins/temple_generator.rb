require 'json'

module Jekyll
  class TemplePageGenerator < Generator
    safe true
    priority :normal

    def generate(site)
      temples = site.data['temples']
      return unless temples&.any?

      Jekyll.logger.info "TempleGenerator:", "#{temples.size}개 페이지 생성 중..."

      temples.each do |temple|
        same_region = temples
          .select { |s| s['region'] == temple['region'] && s['slug'] != temple['slug'] }
          .first(8)
          .map { |s| { 'slug' => s['slug'], 'name' => s['templeName'], 'city' => s['city'], 'image' => s['image'] } }

        # 이전/다음: 같은 지역 내에서 이름 순 정렬 후 순환
        region_ordered = temples
          .select { |s| s['region'] == temple['region'] }
          .sort_by { |s| s['templeName'].to_s }
        idx = region_ordered.index { |s| s['slug'] == temple['slug'] }
        prev_temple = nil
        next_temple = nil
        if idx && region_ordered.size > 1
          p = region_ordered[(idx - 1) % region_ordered.size]
          n = region_ordered[(idx + 1) % region_ordered.size]
          prev_temple = { 'slug' => p['slug'], 'name' => p['templeName'] }
          next_temple = { 'slug' => n['slug'], 'name' => n['templeName'] }
        end

        site.pages << TemplePage.new(site, temple, same_region, prev_temple, next_temple)
      end

      by_region = temples.group_by { |s| s['region'] }
      by_region.each do |region, region_temples|
        slug = region_temples.first['regionSlug']
        site.pages << RegionPage.new(site, region, slug, region_temples)
      end

      site.pages << SearchIndexPage.new(site, temples)

      Jekyll.logger.info "TempleGenerator:", "완료 (#{temples.size}개)"
    end
  end

  class TemplePage < Page
    def initialize(site, temple, same_region, prev_temple, next_temple)
      @site = site
      @base = site.source
      @dir  = "temple/#{temple['slug']}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'temple.html')
      self.data.merge!(temple)
      self.data['layout']      = 'temple'
      self.data['same_region'] = same_region
      self.data['prev_temple'] = prev_temple
      self.data['next_temple'] = next_temple

      self.data['title'] = "#{temple['templeName']} 위치·소개 | #{temple['region']} #{temple['city']} 사찰 정보"
      overview_short = (temple['overview'] || '').to_s
      overview_short = overview_short[0, 80] unless overview_short.empty?
      self.data['description'] = "#{temple['templeName']}(#{temple['region']} #{temple['city']}) 위치, 유래, 이용시간 정보. #{overview_short}"
    end
  end

  class RegionPage < Page
    def initialize(site, region, slug, temples)
      @site = site
      @base = site.source
      @dir  = "region/#{slug}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'region.html')
      self.data['layout']      = 'region'
      self.data['region']      = region
      self.data['region_slug'] = slug
      self.data['temples']     = temples
      self.data['title']       = "#{region} 사찰 총정리 | 가볼만한 절 #{temples.size}곳"
      self.data['description'] = "#{region} 사찰 #{temples.size}곳 총정리! 위치와 유래를 한눈에 확인하세요."
    end
  end

  class SearchIndexPage < Page
    def initialize(site, temples)
      @site = site
      @base = site.source
      @dir  = ''
      @name = 'search_index.json'

      self.process(@name)
      self.data = { 'layout' => nil, 'sitemap' => false }

      index = temples.map do |s|
        {
          'slug' => s['slug'], 'name' => s['templeName'], 'region' => s['region'], 'city' => s['city'],
          'image' => s['image'],
        }
      end

      self.content = index.to_json
    end

    def output   = self.content
    def render(layouts, registers); end
  end
end
