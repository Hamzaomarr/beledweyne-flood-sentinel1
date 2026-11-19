import re
src=open(r'.\scripts\110_make_figures.py',encoding='utf-8').read().split('\n')
exec(compile('\n'.join(src[:52]),'setup','exec'))
import pandas as pd, matplotlib.dates as mdates
c1=json.load(open(os.path.join(DG,'chirps_daily_mm.json'))); c2=json.load(open(os.path.join(DG,'chirps_daily_mm_nov_dec.json')))
cd=pd.DataFrame(c1+c2,columns=['date','mm']).drop_duplicates('date'); cd['date']=pd.to_datetime(cd.date); cd=cd.sort_values('date')
fig,ax=plt.subplots(figsize=(W,2.9)); fig.subplots_adjust(top=0.78,bottom=0.17,left=0.09,right=0.99)
ax.bar(cd.date,cd.mm,width=0.85,color='#9ecae1',edgecolor='none')
s1d=['2023-10-09','2023-10-21','2023-11-02','2023-11-14','2023-11-26','2023-12-08']; opt=['2023-11-12','2023-11-23','2023-11-30']
for d_ in s1d: ax.axvline(pd.Timestamp(d_),color=VERM,lw=1.0)
for d_ in opt: ax.axvline(pd.Timestamp(d_),color=BLUE,lw=1.0,ls=(0,(4,2)))
ax.set_ylabel('Daily rainfall, mm',labelpad=6); ax.set_xlabel('Date in 2023',labelpad=6); ax.yaxis.grid(True); ax.set_xlim(pd.Timestamp('2023-09-14'),pd.Timestamp('2023-12-10'))
ax.xaxis.set_major_locator(mdates.MonthLocator()); ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=0)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
above(ax,[Patch(color='#9ecae1',label='Rainfall, study rectangle mean'),Line2D([0],[0],color=VERM,lw=1.0,label='Sentinel-1 acquisition'),Line2D([0],[0],color=BLUE,lw=1.0,ls=(0,(4,2)),label='UNOSAT optical acquisition')],3,y=1.02)
save(fig,'figS3_rainfall_timeline')

