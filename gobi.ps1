# get the directory of the script
$scriptpath = $MyInvocation.MyCommand.Path
$scriptdir = Split-Path $scriptpath

python3 $scriptdir/gobi.py $args
