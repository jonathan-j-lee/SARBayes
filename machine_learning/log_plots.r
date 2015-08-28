# SARbayes

data_frame = read.table("ISRID-survival.tab", sep="\t", quote="", skip=3, 
    col.names = c("status", "hours", "hdd", "cdd"), 
    colClasses=c(rep("character", 1), rep("numeric", 3)))

keeps = c("cdd", "status")
data_frame = data_frame[keeps]
data_frame = data_frame[complete.cases(data_frame),]
data_frame = transform(data_frame, status=ifelse(status == "DEAD", 0, 1))
#data_frame = data_frame[data_frame$hdd < 10000000,]
summary(data_frame)

logit = glm(status ~ cdd, data=data_frame, family="binomial")
summary(logit)
confint(logit)

png('cdd.png')

plot(
    data_frame$cdd, 
    data_frame$status, 
    xlab="Cooling Degree Days (degrees C)", 
    ylab="Probability of Survival", 
    main="Probability of Survival vs. Cooling Degree Days"
)

curve(
    predict(logit, data.frame(cdd=x), type="resp"), add=TRUE
)

#curve(fitted, add=TRUE)
#lines(data_frame$hours, fitted[, 'lwr'], lty='dotted')
#lines(data_frame$hours, fitted[, 'upr'], lty='dotted')

dev.off()
