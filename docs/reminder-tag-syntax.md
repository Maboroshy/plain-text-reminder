# Reminder tag syntax

!R parses plain text files for reminder tags. Reminder tag starts with `@!` marker.  
!R is highly customizable. Reminder tag marker and most of other settings and syntax, you'll see below, can be changed to whatever you want.

## Reminder tag syntax basics

First word of reminder tag sets reminder time. Consecutive words are reminder text. 

`@!2018-01-01/0:01 Happy New Year` will show "Happy New Year" at the start of 2018 year

!R parses reminder tags as next occurrence of given date and/or time.

`@!01-01/0:01 Happy New Year` will show "Happy New Year" at the start of the next year  
`@!Mon/9:00 Lets get to work` will show "Lets get to work" next Monday at 9 o'clock  
`@!7:00 Wake up` will show "Wake up" tomorrow at 7 o'clock  

You can provide time in 24H format or 12H format with "am" or "pm"  

`@!Mon/18:00 Time to go home` and  
`@!Mon/6:00pm Time to go home` both will show "Time to go home" next Monday at 6 o'clock in the evening  

You can provide time with spaces if you put it inside brackets  

`@!(Monday at 6:00 pm) Time to go home`

If there's no time provided, the reminder will be set to default time, which is 9:00.

`@!01-01 It's new year morning` will show "It's new year morning" next 1st January at 9 o'clock  
`@!Mon Lets get to work` will show "Lets get to work" next Monday at 9 o'clock

Single digit time will be parsed as hours. That, as everything else, can be changed.

`@!7 Wake up` will show "Wake up" tomorrow at 7 o'clock  
`@!9pm` with no text next will show an empty reminder tomorrow at 9 o'clock in the evening  

If there's no time and no date provided, the reminder will be set to tomorrow, default time.

`@! The quickest reminder` will show "The quickest reminder" tomorrow at 9 o'clock  
`@!` with no text next will show an empty reminder tomorrow at 9 o'clock

## Providing time as delta to current time

You can provide time as delta to current time. You should put `+` after reminder tag marker and time unit type after digits.

`@!+1m One minute past`  
`@!+1y Call me next year`  
`@!(+ 1 month 1 day and 12 hours)` will add everything provided  

Delta format also obeys single digit rule.

`@!+1 One hour later`

## Advanced syntax

If you like putting reminder tags to the middle of a text line, you may want cut the text of your reminder.   
By default the reminder text length is limited to 20 words. You can cut it manually by putting `.` or `!` to the end of reminder text.

`Not reminder text @!12:00 Reminder text! Not reminder text`

You can put multiple reminder tags to the single line, but that may affect reminder text if one of them is deleted.

`@! An empty reminder @!+1day Another day. in the office` can turn into  
`@! An empty reminder in the office`

You can mark a part of text as a "reminder block" by putting `@!(((` at the beginning of such block and `)))` at the end. If there's no block end marker, the block goes till the end of text. Inside reminder block reminder tags use no marker. Multiple reminder tags per line is not supported.
```
@!(((
2018-01-01/0:01 Happy New Year
(Monday at 6:00 pm) Time to go home
+1m One minute past
12:00 Reminder text! Not reminder text
```
