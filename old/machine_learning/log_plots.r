# SARbayes

data_frame = read.table("ISRID-survival.tab", sep="\t", quote="", skip=3, 
    col.names = c("status", "bmi"), 
    colClasses=c(rep("character", 1), rep("numeric", 1)))

keeps = c("status", "bmi")
data_frame = data_frame[keeps]
data_frame = data_frame[complete.cases(data_frame),]
data_frame = transform(data_frame, status=ifelse(status == "DEAD", 0, 1))
#data_frame = data_frame[data_frame$hdd < 10000000,]
summary(data_frame)

logit = glm(status ~ bmi, data=data_frame, family="binomial")
summary(logit)
confint(logit)

png('bmi-25.png')

plot(
    data_frame$bmi, 
    data_frame$status, 
    xlab="BMI (kg/m^2)", 
    ylab="Probability of Survival", 
    main="Probability of Survival vs. BMI"
)

curve(
    predict(logit, data.frame(bmi=x), type="resp"), add=TRUE
)

#curve(fitted, add=TRUE)
#lines(data_frame$hours, fitted[, 'lwr'], lty='dotted')
#lines(data_frame$hours, fitted[, 'upr'], lty='dotted')

dev.off()
