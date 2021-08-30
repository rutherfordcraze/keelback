import os, pathlib, time, shutil, errno
import markdown, pystache
from datetime import datetime
# from slugify import slugify

DIR_CONTENT     = "Content"
DIR_TEMPLATES   = "Templates"
DIR_EXPORT      = "Export"
DIR_STATIC      = "Static"

META_DELIMITER  = "====="

###

def slugify(string):
    return string.lower()

class Page:
    def __init__(
        self,
        path,
        title,
        ctime = None
        ):
        self.path = path
        self.title = title
        self.slug = slugify(title)
        self.ctime = ctime
        self.split = None

    def __repr__(self):
        return "page:" + self.slug

    def split_content(self):
        if not self.split:
            with open(os.path.join(self.path, self.title + ".txt"), 'r') as f:
                split = f.read().strip().split(META_DELIMITER, 1)
            # Split[0] will *always* be the content
            # Split[1] will be meta only if present
            self.split = (split[1],
                          split[0]) if len(split) > 1 else (split[0], {})
        return self.split


    @property
    def content(self):
        print(self.meta)
        return self.split_content()[0]

    @property
    def meta(self):
        meta_dict = {}
        if self.split_content()[1]:
            meta_str = self.split_content()[1]
            lines = meta_str.split("\n")
            for line in lines:
                line_split = line.split(": ", 1)
                if len(line_split) > 1:
                    k, v = line_split[0], line_split[1]
                    meta_dict[k.lower()] = v
            if 'title' not in meta_dict:
                meta_dict['title'] = self.slug
            return meta_dict
        return {'title': self.slug}

    @property
    def body(self):
        if self.content:
            template = markdown.markdown(self.content)
            r = pystache.Renderer()
            return r.render(template, dict(categories=categories))
        return ""

    @property
    def timestamp(self):
        if self.ctime:
            return datetime.utcfromtimestamp(self.ctime).strftime('%b %Y')
        return None
    

    @property
    def crumb(self):
        path = self.path.split("/")
        if self.slug == "index":
            crumb = []
        else:
            crumb = [get_link(pages["index"])]
            for point in path[1:]:
                if point in categories:
                    # hide categories if there is a page
                    # with the same name as them
                    if point != self.slug:
                        crumb.append(get_link(categories[point]))
        crumb.append(get_link(self, True))
        return " / ".join(crumb)
    

    @property
    def props(self):
        return dict(
            vars(self),
            body = self.body,
            meta = self.meta,
            crumb = self.crumb,
            timestamp = self.timestamp)

    @property
    def html(self):
        with open(os.path.join(DIR_TEMPLATES, "page.html"), 'r') as f:
            template = f.read()

        r = pystache.Renderer()
        return r.render(template, self.props)
    

class Category:
    def __init__(
        self,
        path,
        title
        ):
        self.path = path
        self.title = title.capitalize()
        self.slug = slugify(title)
        self.pages = []

    def __repr__(self):
        return "category:" + self.slug

    def add_page(self, page):
        self.pages.append(page)

    @property
    def crumb(self):
        path = self.path.split("/")
        crumb = [get_link(pages["index"])]
        for point in path[1:-1]:
            if point in categories:
                crumb.append(get_link(categories[point]))
        crumb.append(get_link(self, True))
        return " / ".join(crumb)

    @property
    def contents(self):
        ol = ["<ol class='category'>"]
        ul = ["<ul class='category'>"]
        # put recent posts on top
        # self.pages.sort(key=lambda x: x.ctime, reverse=True)
        if self.pages:
            if self.pages[0].ctime:
                self.pages.sort(key=lambda x: (x.ctime, x.title), reverse=True)
                for page in self.pages:
                    ol.append("<li>")
                    ol.append(get_link(page))
                    if page.timestamp:
                        ol.append("<span class='timestamp'>")
                        ol.append(page.timestamp)
                        ol.append("</span>")
                    ol.append("</li>")
                ol.append("</ol>")
                return '\n'.join(ol)
            else:
                self.pages.sort(key=lambda x: x.title, reverse=False)
                for page in self.pages:
                    ul.append("<li>")
                    ul.append(get_link(page))
                    if page.timestamp:
                        ul.append("<span class='timestamp'>")
                        ul.append(page.timestamp)
                        ul.append("</span>")
                    ul.append("</li>")
                ul.append("</ul>")
                return '\n'.join(ul)
        return None
    

    @property
    def props(self):
        return dict(
            vars(self),
            crumb = self.crumb,
            contents = self.contents)

    @property
    def html(self):
        with open(os.path.join(DIR_TEMPLATES, "category.html"), 'r') as f:
            template = f.read()

        r = pystache.Renderer()
        return r.render(template, self.props)

###

def get_content():
    pages = {}
    categories = {}
    for path, dirs, files in os.walk(DIR_CONTENT):
        current_dir = path.split('/')[-1]
        if current_dir != "Content":
            categories[current_dir] = Category(path, current_dir)
        for file in files:
            if file.endswith(".txt"):
                title = file[:-4]
                
                if current_dir == "articles":
                    fname = pathlib.Path(os.path.join(path, file))
                    ctime = int(fname.stat().st_mtime)
                else:
                    ctime = None

                new_page = Page(path, title, ctime)
                pages[new_page.slug] = new_page

                if current_dir != "Content":
                    categories[current_dir].add_page(new_page)
    return (pages, categories)


def get_link(instance, highlit = False):    
    template = "<a href='/{slug}.html'>{title}</a>"
    if highlit:
        template = "<a href='/{slug}.html' class='highlit'>{title}</a>"
    return template.format(slug=instance.slug, title=instance.title)


def assemble(slug):
    if slug not in pages and slug not in categories:
        return "404"
    elif slug == "" or slug == "/":
        slug = "index"

    if slug in pages:
        page = pages[slug]
        props = dict(page = page.html, title = page.title, meta = page.meta)
    elif slug in categories:
        category = categories[slug]
        props = dict(page = category.html, title = category.title)

    with open(os.path.join(DIR_TEMPLATES, "layout.html"), 'r') as f:
        template = f.read()

    r = pystache.Renderer()
    return r.render(template, props)


def clear_export_folder():
    shutil.rmtree(os.path.abspath(DIR_EXPORT))


def tree_clone(source, destination):
    try:
        shutil.copytree(source, destination)
    except OSError as e:
        if e.errno == errno.ENOTDIR:
            shutil.copy(source, destination)
        else:
            print('Directory not copied:\n{}'.format(str(e)))


def copy_static():
    source = os.path.abspath(os.path.join(DIR_STATIC))
    destination = os.path.abspath(os.path.join(DIR_EXPORT, 'static'))
    tree_clone(source, destination)


def output(slug):
    html = assemble(slug)

    with open(os.path.join(DIR_EXPORT, slug + ".html"), 'w') as f:
        f.write(html)


def export_static_site():
    counter = 0
    start = time.time()

    global pages, categories
    pages, categories = get_content()

    clear_export_folder()
    copy_static()

    for slug in categories.keys():
        output(slug)
        counter += 1

    for slug in pages.keys():
        output(slug)
        counter += 1

    stop = time.time()
    elapsed = int((stop - start) * 1000)

    print("[KEELBACK] Exported {pages} pages in {time} ms.".format(
        pages=counter,
        time=elapsed))

export_static_site()