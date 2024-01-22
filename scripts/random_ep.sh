#!/bin/bash

# Function to display usage message
usage () {
  echo "Usage: $0 play|scene [season_number [episode_number]]"
  exit 1
}

# Make sure the second argument is 'play' or 'scene' and error if not
if [ $# -gt 0 ]; then
  if [ "$1" != "play" ] && [ "$1" != "scene" ]; then
    usage
  fi
fi

# Now a boolean if they chose 'play'
if [ "$1" == "play" ]; then
  play=true
else
  play=false
fi

# Mount the encrypted disk image
if [ ! -d "/Volumes/SAUL" ]; then
    hdiutil attach -stdinpass /Users/benschwartz/BACKUP/media/saul/BCS.dmg
fi

# Check if the volume is successfully mounted
if [ ! -d "/Volumes/SAUL" ]; then
  echo "Failed to mount the disk image. Exiting."
  exit 1
fi

# Navigate to the mounted volume
cd /Volumes/SAUL


extract_scene() {
  # Get the season and episode numbers
  episodePath=$1
  duration='00:01:00'
  fps='1/4'
  output_dir='extracted_scene'

  python3 extract_scene.py $episodePath $duration $fps $output_dir
  echo "Extracted scene from $episodePath" > $output_dir/README.md
  open $output_dir
}

# Function to pick a random episode from a given season
pick_random_episode () {
  season=$1
  episode=$(ls $season | shuf -n 1)
  echo "Opening random episode $episode from season $season"
  if [ "$play" = true ]; then
    open "$season/$episode"
  else
    extract_scene "$season/$episode"
  fi
  
}

# Check number of arguments
if [ $# -gt 3 ]; then
  usage
fi

if [ $# -eq 3 ]; then
  seasonNumber=$2
  episodeNumber=$3

  if [[ $seasonNumber -ge 1 && $seasonNumber -le 6 ]]; then
    season="s$seasonNumber"
    
    maxEpisode=10
    if [ "$seasonNumber" -eq 6 ]; then
      maxEpisode=13
    fi

    if [[ $episodeNumber -ge 1 && $episodeNumber -le $maxEpisode ]]; then
      episode=$(printf "%s%02d.mp4" $seasonNumber $episodeNumber)
      echo "Opening episode $episode from season $season"
      if [ "$play" = true ]; then
        open "$season/$episode"
      else
        extract_scene "$season/$episode"
      fi
    else
      usage
    fi
  else
    usage
  fi
elif [ $# -eq 2 ]; then
  seasonNumber=$2

  if [[ $seasonNumber -ge 1 && $seasonNumber -le 6 ]]; then
    season="s$seasonNumber"
    pick_random_episode $season
  else
    usage
  fi
else
  # Pick a random season
  randomSeason=$(ls | shuf -n 1)
  pick_random_episode $randomSeason
fi

