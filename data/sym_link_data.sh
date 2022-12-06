for file in /home/mauricechiu/crowdbot_dataset/crowdbot_dataset/uncompressed/*
do 
    echo "linking $file ..."
    ln -s $file /home/mauricechiu/crowdbot-evaluation-tools/data
    echo "done..."
    echo ""
done
echo "Finished linking data"