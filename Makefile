bot: 
	uvicorn main:app --reload

production:
	uvicorn main:app

git:
	git add . && git commit && git push


