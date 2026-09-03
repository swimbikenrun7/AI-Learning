# Good commands

## git

### Session start
git pull

### Session end
git status
git add .
git commit -m "description of changes"
git show --stat                     # to verify which files included in latest local commit
git push

### Branching
git branch                          # displays branches with * by current branch
git branch –vv                      # identifies current branch
git remote -v			                  # where does the repo sync
git switch -c XXXXXX                # create a new branch "XXXXXX"
git switch XXXXXX                   # switch to branch "XXXXXX"
git merge XXXXXX                    # from current branch, merges "XXXXXX"
git branch -d XXXXXX                # deletes branch "XXXXXX"

### Misc
git log --oneline --decorate -5     # returns 5 most recent commits
git restore XXXXXX                  # discards uncommitted changes to the file
git status --ignored                # checks for files/directories in .gitignore
git check-ignore -v __pycache__/*   # if there are matching files, git tells you which .gitignore rule cause them 
                                    # to be ignored
git rm -r --cached __pycache__      # removes tracking of pycache files in git

## Powershell
get-location                        # returns active directory
pwd                                 # returns active directory
dir                                 # returns directory contents
cd xxxx                             # moves into specified folder
..                                  # parent folder
.                                   # current location
mkdir xxxx                          # create a folder
new-item xxx.aaa                    # create file from terminal
New-Item XXX.txt -ItemType File     # create text file from terminal
rename-item XXX.aaa YYY.aaa         # rename file from terminal
copy-item xxx.aaa xxx-copy.aaa      # copy file from terminal
cp                                  # copy file from terminal
remove-item xxx.aaa                 # delete file from terminal
rm                                  # delete file from terminal
mv                                  # move item from terminal

get-childitem -recurse -directory -filter "XXX" # returns directory(s) named "XXX"     
get-childitem -recurse -filter "*.XXX"          # returns location of files with filetype ".XXX"

code xxx.aaa                        # opens specified file in vscode

## Ubuntu (wsl)
wsl.exe                             # start linux
ls                                  # "get-location"
ls -la                              # "get-childitem"
sudo                                # "run this command with elevated administrative priveleges"
journalctl                          # returns....
systemctl                           # does....
Ctrl+c                              # ends current process

## Tmux
tmux attach			                  # attach to ongoing tmux session
Ctrl+b c			                    # new window
Ctrl+b n			                    # next window
Ctrl+b p                          # previous window
Ctrl+b d			                    # detach from tmux
Ctrl+b %			                    # split vertically
Ctrl+b "			                    # split horizontally
Ctrl+b x			                    # kill pane
Ctrl+b [			                    # enter copy mode
Ctrl+b ]			                    # paste copied text in tmux
exit				                      # closes shell/process in pane

## hunk
hunk diff			                    # displays a side-by-side view of the diff for unstaged changes
hunk diff --staged		            # same as above but for staged changes

## tailscale
ssh josh@omarchy		              # connect to Desktop via tailscale

## Openclaw
openclaw --help                                                 # returns a list of commands
openclaw tui                                                    # launches the openclaw terminal interface
openclaw status                                                 # returns information on current status
openclaw security audit                                         # returns information and recommendations
openclaw config set gateway.mode local                          # change gateway mode to local
openclaw config get gateway.mode                                # see gateway mode (verify - should return local)
journalctl --user -u openclaw-gateway.service -n 200 --no-pager # returns a stream of data on the gateway service
systemctl --user restart openclaw-gateway.service               # restart gateway service
openclaw gateway status                                         # returns the status of openclaw gateway
openclaw gateway status --deep --require-rpc                    # returns a detailed log of the gateway
openclaw gateway probe                                          # returns specifics of gateway connection
openclaw logs --follow                                          # returns list of recent and ongoing system actions
openclaw doctor                                                 # assesses the installation and runs a wizard to
                                                                # correct issues
openclaw doctor --repair                                        # repairs the current installation automatically
openclaw models list                                            # returns available models
export OLLAMA_API_KEY="ollama-local"                            # opts in to allow openclaw to see ollama models
openclaw models set XXXXX/XXXXXXX                               # sets model "provider/model" as default
openclaw config set models.providers.ollama.models '[{"id":"qwen2.5-coder:7b","name":"qwen2.5-coder:7b"}]' --strict-json --merge
openclaw agents list                                            # returns details of the current (main) agent
/agent XXX                                                      # switch to agent XXX

## Ollama
ollama pull qwen2.5-coder:7b        # pull qwen model for laptop
ollama run qwen2.5-coder:7b         # run qwen model for laptop
ollama pull qwen2.5-coder:14b       # pull qwen model for desktop
ollama run qwen2.5-coder:14b        # run qwen model for desktop
ollama --version                    # returns ollama version
ollama list                         # returns downloaded models
/bye                                # end ollama session

## Ruff
ruff --version                      # returns ruff version
ruff check .                        # ruff static tests everything in the folder location
ruff format --check .               # ruff describes whether formatting would change but does not execute
