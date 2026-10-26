#!/bin/bash
# NOTE: research script as run on 2026-10-26; paths refer to the research sandbox.
S=//webapp/tg-research/pubsim; rm -rf $S; mkdir -p $S; cd $S || exit 1
git init -q --bare -b main remote.git
mkdir human && cd human && git init -q -b main && git config user.email h@x && git config user.name human
mkdir -p tgproxy templates .github/workflows; echo x > tgproxy/__main__.py; echo t > templates/README.md; echo w > .github/workflows/update.yml; echo "src readme" > README.md
git add -A && git commit -qm "feat: source" && git remote add origin "$S/remote.git" && git push -q origin main || exit 1
cd ..
export OUT_MARK="[auto-output]" OUTPUT_PATHS="verified fast stable resilient faketls secure classic all countries top50.txt index.json health.json state.json README.md README_FA.md"
run_bot(){
  rm -rf bot; git clone -q --depth=2 "file://$S/remote.git" bot || return 1; cd bot
  git config user.email b@x; git config user.name bot
  mkdir -p verified resilient; echo "tg://$2" > verified/tg.txt; echo "tg://$2" > resilient/tg.txt; echo "tg://$2" > top50.txt; echo "{}" > health.json
  echo "{\"funnel\":{\"verified_links\":$2,\"verified_servers\":1}}" > index.json; echo "generated readme $2" > README.md
  [ -n "$3" ] && eval "$3"
  bash -e //webapp/tg-research/publish_step.sh > ../log_$1.txt 2>&1; rc=$?; cd ..; echo "$1 rc=$rc: $(grep -E '✅|❌|⚠️|no change' log_$1.txt | tail -2 | tr '\n' ' ')"; }
run_bot r1 10
run_bot r2 20
echo "== log after 2 bot runs:"; git -C remote.git log --format='  %h %s' main
cd human; git pull -q --rebase origin main; echo y >> tgproxy/__main__.py; git commit -qam "fix: human change"; git push -q origin main; cd ..
run_bot r3 30
echo "== log after human commit + bot run:"; git -C remote.git log --format='  %h %s' main
echo "== tip src: $(git -C remote.git show main:tgproxy/__main__.py | tr '\n' ' ')  verified: $(git -C remote.git show main:verified/tg.txt)  README: $(git -C remote.git show main:README.md)"
run_bot r4 30 ""
echo "== negative: missing resilient output must abort, tip unchanged"
before=$(git -C remote.git rev-parse main); run_bot r5 40 "rm -rf resilient"; after=$(git -C remote.git rev-parse main); [ "$before" = "$after" ] && echo "  tip unchanged ✓" || echo "  TIP CHANGED ✗"
echo "== race: human pushes a source change AFTER the bot fetched (lease must protect it)"
before=$(git -C remote.git rev-parse main)
run_bot r6 50 "( cd $S/human && git pull -q --rebase origin main && echo z >> tgproxy/__main__.py && git commit -qam 'fix: racing human' && git push -q origin main )"
git -C remote.git log --format='  %h %s' main | head -4
echo "  racing human commit present on remote: $(git -C remote.git log --format=%s main | grep -c 'racing human')"
