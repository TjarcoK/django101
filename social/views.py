from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.db.models import Q
from social.models import Post, Comment, User
# Create your views here.

def index(request):
	return render(request, 'social/index.html')

def social_login(request):
	check = _check_post_request(request, ['username', 'password'])
	if check[0]:
		user = authenticate(username=request.POST['username'], password=request.POST['password'])
		if user is not None:
			login(request, user)
			return HttpResponseRedirect(reverse('social:home'))
		else:
			return HttpResponseBadRequest("The combination of username and password does not exist. ")		
	else:
		return HttpResponseBadRequest(check[1])

def social_register(request):
	new_user = False
	error = False
	if request.method == 'POST':
		check = _check_post_request(request, ["username", "email", "password"])
		if check[0]:
			try:
				user = User.objects.create_user(request.POST['username'], request.POST['email'], request.POST['password'])
				user.save()
				new_user = True
			except:
				error = True
		else:
			HttpResponseBadRequest(check[1])	
	return render(request, 'social/register.html', {'new_user': new_user, 'error': error})			

@login_required
def home(request):
	if request.method == 'GET':
		posts = Post.objects.all()
	elif request.method == 'POST':
		check = _check_post_request(request, ['search_terms'])
		if check[0]:
			search_terms = request.POST['search_terms']
			#search in posts and comments
			q_comment = Q(comment__text__icontains=search_terms)
			q_text = Q(text__icontains=search_terms)
			posts = Post.objects.filter(comment__text__icontains=search_terms) | Post.objects.filter(text__icontains=search_terms)
			# posts = Post.objects.filter(q_comment | q_text)
			posts = posts.distinct()
		else:
			return HttpResponseBadRequest(check[1])
	posts = posts.order_by('-date_time')
	return render(request, 'social/home.html', {'posts': posts, 'user': request.user})

@login_required
def add_post(request):
	check = _check_post_request(request, ['text'])
	if check[0]:
		new_post = Post()
		new_post.text = request.POST['text']
		new_post.poster = request.user
		if 'photo' in request.FILES and request.FILES['photo'] is not None:
			new_post.photo = request.FILES['photo']
		new_post.save()
		return HttpResponseRedirect(reverse('social:home'))
	else:
		return HttpResponseBadRequest(check[1])

@login_required
def delete_post(request, post_id):
	post = Post.objects.get(pk=post_id)
	if request.user != post.poster:
		return HttpResponseForbidden("You can only delete your own posts!")
	else:
		post.delete()
		return HttpResponseRedirect(reverse('social:home'))

@login_required
def add_comment(request):
	check = _check_post_request(request, ['comment', 'post_id'])
	if check[0]:
		new_comment = Comment()
		new_comment.poster = request.user
		new_comment.text = request.POST['comment']
		try:
			post = Post.objects.get(pk=request.POST['post_id'])
			new_comment.post = post
		except Post.DoesNotExist:
			return HttpResponseBadRequest("Ther is no Post with id {}".format(request.POST['post_id']))
		new_comment.save()
		return HttpResponseRedirect(reverse('social:home'))
	else:
		return HttpResponseBadRequest(check[1])	

@login_required
def profile(request):
	return render(request, 'social/profile.html', {'user': request.user})					

def _check_post_request(request, keys):
	#Check the request method
	if request.method != 'POST':
		return (False, "This method should be called with a POST method!")

	for key in keys:
		if key not in request.POST:
			return (False, "The POST request should contain a {} field".format(key))
		if not request.POST[key]:
			return (False, "The {} field cannot be empty!".format(key))

	return (True, "Everything is alright!")				


