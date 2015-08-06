# SARbayes

data_frame = read.table("ISRID-survival.tab", sep="\t", quote="", skip=3, 
    col.names = c("status", "category", "sex", "age", "hours", 
        "temp_max", "temp_min", "wind_speed", "snow", "rain"), 
    colClasses=c(rep("character", 3), rep("numeric", 7)))

keeps = c("temp_max", "temp_min", "status")
data_frame = data_frame[keeps]
data_frame = data_frame[complete.cases(data_frame),]
data_frame = transform(data_frame, status=ifelse(status == "DEAD", 0, 1))
summary(data_frame)

logit = glm(status ~ temp_max + temp_min, data=data_frame, family="binomial")
summary(logit)
confint(logit)

png('temp_plot.png')

plot(
    data_frame$temp_max, 
    data_frame$status, 
    xlab="Temperature", 
    ylab="Probability of Survival", 
    main="Survival Rate"
)

curve(
    predict(
        logit, 
        data.frame(temp_max=x), 
        type="resp"
    ), 
    add=TRUE
)

dev.off()
