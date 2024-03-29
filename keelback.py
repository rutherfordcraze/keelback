import os, pathlib, time, shutil, errno, json
from posixpath import abspath
import markdown, pystache
from datetime import datetime

CONFIG_FILE = "./config.json"

###


def slugify(string):
    return string.lower()


class Page:
    def __init__(self, path, title, template_dir, ctime=None, meta_delimiter="====="):
        self.path = path
        self.title = title
        self.slug = slugify(title)
        self.template_dir = template_dir
        self.ctime = ctime
        self.split = None
        self.meta_delimiter = meta_delimiter

    def __repr__(self):
        return "page:" + self.slug

    def split_content(self):
        if not self.split:
            with open(os.path.join(self.path, self.title + ".txt"), "r") as f:
                split = f.read().strip().split(self.meta_delimiter, 1)
            # Split[0] will *always* be the content
            # Split[1] will be meta only if present
            self.split = (split[1], split[0]) if len(split) > 1 else (split[0], {})
        return self.split

    @property
    def link(self):
        template = "<a href='./{slug}.html'>{title}</a>"
        if "title" in self.meta:
            return template.format(slug=self.slug, title=self.meta["title"])
        return template.format(slug=self.slug, title=self.title)

    @property
    def content(self):
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
            if "title" not in meta_dict:
                meta_dict["title"] = self.slug
            return meta_dict
        return {"title": self.slug}

    @property
    def body(self):
        if self.content:
            template = markdown.markdown(self.content)
            r = pystache.Renderer()
            return r.render(template, dict(categories=categories, pages=pages))
        return ""

    @property
    def time(self):
        if self.meta:
            if "date" in self.meta:
                return datetime.strptime(self.meta["date"], "%d-%m-%Y").timestamp()
        if self.ctime:
            return self.ctime
        return None

    @property
    def timestamp(self):
        if self.meta:
            if "date" in self.meta:
                return datetime.strptime(self.meta["date"], "%d-%m-%Y").strftime(
                    "%b %Y"
                )
        if self.ctime:
            return datetime.utcfromtimestamp(self.ctime).strftime("%b %Y")
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
            body=self.body,
            meta=self.meta,
            crumb=self.crumb,
            timestamp=self.timestamp,
        )

    @property
    def html(self):
        with open(os.path.join(self.template_dir, "page.html"), "r") as f:
            template = f.read()

        r = pystache.Renderer()
        return r.render(template, self.props)


class Category:
    def __init__(self, path, title, template_dir):
        self.path = path
        self.title = title.capitalize()
        self.slug = slugify(title)
        self.pages = []
        self.template_dir = template_dir

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
            if self.pages[0].time:
                self.pages.sort(key=lambda x: (x.time, x.title), reverse=True)
                for page in self.pages:
                    ol.append("<li>")
                    # ol.append(get_link(page))
                    ol.append(page.link)
                    if page.timestamp:
                        ol.append("<span class='timestamp'>")
                        ol.append(page.timestamp)
                        ol.append("</span>")
                    ol.append("</li>")
                ol.append("</ol>")
                return "\n".join(ol)
            else:
                self.pages.sort(key=lambda x: x.title, reverse=False)
                for page in self.pages:
                    ul.append("<li>")
                    # ul.append(get_link(page))
                    ul.append(page.link)
                    if page.timestamp:
                        ul.append("<span class='timestamp'>")
                        ul.append(page.timestamp)
                        ul.append("</span>")
                    ul.append("</li>")
                ul.append("</ul>")
                return "\n".join(ul)
        return None

    @property
    def props(self):
        return dict(vars(self), crumb=self.crumb, contents=self.contents)

    @property
    def html(self):
        with open(os.path.join(self.template_dir, "category.html"), "r") as f:
            template = f.read()

        r = pystache.Renderer()
        return r.render(template, self.props)


###


def get_content(content_dir: str, template_dir: str, meta_delimiter: str):
    pages = {}
    categories = {}
    for path, dirs, files in os.walk(content_dir):
        current_dir = path.split("/")[-1]
        if current_dir.lower() != "content":
            categories[current_dir] = Category(path, current_dir, template_dir)
        for file in files:
            if file.endswith(".txt"):
                title = file[:-4]

                if current_dir.lower() == "articles":
                    fname = pathlib.Path(os.path.join(path, file))
                    ctime = int(fname.stat().st_mtime)
                else:
                    ctime = None

                new_page = Page(path, title, template_dir, ctime, meta_delimiter)
                pages[new_page.slug] = new_page

                if current_dir.lower() != "content":
                    categories[current_dir].add_page(new_page)
    return (pages, categories)


def get_link(instance, highlit=False):
    template = "<a href='./{slug}'>{title}</a>"
    if highlit:
        template = "<a href='./{slug}' class='highlit'>{title}</a>"
    return template.format(slug=instance.slug, title=instance.title)


def assemble(slug, template_dir):
    if slug not in pages and slug not in categories:
        return "404"
    elif slug == "" or slug == "/":
        slug = "index"

    if slug in pages:
        page = pages[slug]
        props = dict(
            page=page.html,
            title=page.title,
            meta=page.meta,
            pages=pages,
            buildtime=buildtime,
        )
    elif slug in categories:
        category = categories[slug]
        props = dict(
            page=category.html, title=category.title, pages=pages, buildtime=buildtime
        )

    with open(os.path.join(template_dir, "layout.html"), "r") as f:
        template = f.read()

    r = pystache.Renderer()
    return r.render(template, props)


def tree_clone(source: abspath, destination: abspath):
    try:
        shutil.copytree(source, destination)
    except OSError as e:
        if e.errno == errno.ENOTDIR:
            shutil.copy(source, destination)
        else:
            print("Directory not copied:\n{}".format(str(e)))


def copy_static(source: str, destination: str):
    source = os.path.abspath(os.path.join(source))
    destination = os.path.abspath(os.path.join(destination, "static"))
    tree_clone(source, destination)


def output(slug: str, template_dir: str, destination: str):
    html = assemble(slug, template_dir)

    with open(os.path.join(destination, slug + ".html"), "w") as f:
        f.write(html)


# def load_config():
#     with open(CONFIG_FILE, "r") as f:
#         config = json.load(f)

#     # todo: don’t hard code these
#     global DIR_CONTENT, DIR_TEMPLATES, DIR_EXPORT, DIR_STATIC, META_DELIMITER

#     DIR_CONTENT = config["dir_content"]
#     DIR_TEMPLATES = config["dir_templates"]
#     DIR_EXPORT = config["dir_export"]
#     DIR_STATIC = config["dir_static"]
#     META_DELIMITER = config["meta_delimiter"]


def export_static_site(
    content_directory: str,
    static_directory: str,
    template_directory: str,
    export_directory: str,
    meta_delimiter: str,
):
    counter = 0
    start = time.time()

    # load_config()

    global pages, categories
    pages, categories = get_content(
        content_directory, template_directory, meta_delimiter
    )

    global buildtime
    buildtime = datetime.now().strftime("%Y·%m·%d %H:%M")

    # Clear the export dir before copying static files
    shutil.rmtree(os.path.abspath(export_directory))
    copy_static(static_directory, export_directory)

    for slug in categories.keys():
        output(slug, template_directory, export_directory)
        counter += 1

    for slug in pages.keys():
        output(slug, template_directory, export_directory)
        counter += 1

    stop = time.time()
    elapsed = int((stop - start) * 1000)

    print(
        "[KEELBACK] Exported {pages} pages in {time} ms.".format(
            pages=counter, time=elapsed
        )
    )


if __name__ == "__main__":
    export_static_site()
