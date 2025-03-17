from django.urls import path
from .views import NewsListView,SportsListView,EconomyListView,PoliticsListView,LifestyleListView,EntertainmentListView
from . import views
from .views import like_article, dislike_article, toggle_favorite


urlpatterns = [
	path('scrape/', views.scrape, name="scrape"),
	path('scrape1/', views.scrape1, name="scrape1"),
	path('scrape2/', views.scrape2, name="scrape2"),
	path('scrape3/', views.scrape3, name="scrape3"),
	path('scrape4/', views.scrape4, name="scrape4"),
	path('scrape5/', views.scrape5, name="scrape5"),
	path('getnews/', NewsListView.as_view(), name='home'),
	path('geteconomynews/', EconomyListView.as_view(), name='economy_home'),
	path('getsportsnews/', SportsListView.as_view(), name='sports_home'),
	path('getpoliticsnews/', PoliticsListView.as_view(), name='politics_home'),
	path('getlifestylenews/', LifestyleListView.as_view(), name='lifestyle_home'),
	path('getentertainmentnews/', EntertainmentListView.as_view(), name='entertainment_home'),
	path('menu/', views.menu_list, name='menu'),
	path('', views.home1, name="starter"),
    path('like/<int:article_id>/', like_article, name='like_article'),
    path('dislike/<int:article_id>/', dislike_article, name='dislike_article'),
    path('favorite/<int:article_id>/', toggle_favorite, name='toggle_favorite'),
]