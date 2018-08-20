.PHONY: clean

all: wheel


clean: 
	rm -rf build dist wrappa.egg-info

wheel:
	python setup.py bdist_wheel



