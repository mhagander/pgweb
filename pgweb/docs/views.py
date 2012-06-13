from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import TemplateDoesNotExist, loader, Context
from django.contrib.auth.decorators import login_required

from decimal import Decimal

from pgweb.util.decorators import ssl_required
from pgweb.util.contexts import NavContext
from pgweb.util.helpers import simple_form

from pgweb.core.models import Version

from models import DocPage, DocComment
from forms import DocCommentForm

def docpage(request, version, typ, filename):
	loaddate = None
	# Get the current version both to map the /current/ url, and to later
	# determine if we allow comments on this page.
	currver = Version.objects.filter(current=True)[0].tree
	if version == 'current':
		ver = currver
	elif version == 'devel':
		if not typ == 'static':
			return HttpResponseRedirect("/docs/devel/static/%s.html" % filename)
		ver = Decimal(0)
		loaddate = Version.objects.get(tree=Decimal(0)).docsloaded
	else:
		ver = Decimal(version)

	if ver < Decimal("7.1") and ver > Decimal(0):
		extension = "htm"
	else:
		extension = "html"

	if ver < Decimal("7.1") and ver > Decimal(0):
		indexname = "postgres.htm"
	elif ver == Decimal("7.1"):
		indexname = "postgres.html"
	else:
		indexname = "index.html"

	fullname = "%s.%s" % (filename, extension)
	page = get_object_or_404(DocPage, version=ver, file=fullname)
	versions = DocPage.objects.filter(file=fullname).extra(select={'supported':"COALESCE((SELECT supported FROM core_version v WHERE v.tree=version), 'f')"}).order_by('-supported', '-version').only('version', 'file')

	if typ=="interactive":
		comments = DocComment.objects.filter(version=ver, file=fullname, approved=True).order_by('posted_at')
	else:
		comments = None

	return render_to_response('docs/docspage.html', {
		'page': page,
		'supported_versions': [v for v in versions if v.supported],
		'unsupported_versions': [v for v in versions if not v.supported],
		'title': page.title,
		'doc_type': typ,
		'comments': comments,
		'can_comment': (typ=="interactive" and ver==currver),
		'doc_index_filename': indexname,
		'loaddate': loaddate,
	})

def docsrootpage(request, version, typ):
	return docpage(request, version, typ, 'index')

def redirect_root(request, version):
	return HttpResponseRedirect("/docs/%s/static/" % version)

@ssl_required
@login_required
def commentform(request, itemid, version, filename):
	return simple_form(DocComment, itemid, request, DocCommentForm,
		fixedfields={
			'version': version,
			'file': filename,
		},
		redirect='/docs/comment_submitted/'
	)
