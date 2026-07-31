# Good commands

## git

### Session start
git pull

### Session end
git status
git add .
git commit -m "description of changes"
git push

## Powershell
get-location                        % returns active directory
pwd                                 % returns active directory
dir                                 % returns directory contents
cd xxxx                             % moves into specified folder
..                                  % parent folder
.                                   % current location
mkdir xxxx                          % create a folder
new-item xxx.aaa                    % create file from terminal
New-Item XXX.txt -ItemType File     % create text file from terminal
rename-item XXX.aaa YYY.aaa         % rename file from terminal
copy-item xxx.aaa xxx-copy.aaa      % copy file from terminal
cp                                  % copy file from terminal
remove-item xxx.aaa                 % delete file from terminal
rm                                  % delete file from terminal
mv                                  % move item from terminal

code xxx.aaa                        % opens specified file in vscode

## Ollama
ollama pull qwen2.5-coder:7b        % pull the latest qwen model
ollama run qwen2.5-coder:7b         % run the stored qwen model
ollama --version                    % returns ollama version
ollama list                         % returns downloaded models
/bye                                % end ollama session