.PHONY: start status list verify test
start:
	./bin/learn start $(MODULE)
status:
	./bin/learn status
list:
	./bin/learn list
verify:
	./scripts/agent-verify.sh
test:
	python3 -m unittest discover -s tests -v
