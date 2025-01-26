bot: 
	pipenv run uvicorn main:app

production:
	uvicorn main:app

git:
	git add . && git commit && git push

requirements:
	pip freeze > requirements.txt
