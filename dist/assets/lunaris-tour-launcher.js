(()=>{
  if(document.querySelector('.lunaris-tour-launcher') || location.pathname.replace(/\/+$/,'')==='/tour')return;
  const link=document.createElement('a');link.className='lunaris-tour-launcher';link.href='/tour/';link.setAttribute('aria-label','Explore LUNARIS guided walkthrough');
  link.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true"><path d="m8 5 11 7-11 7V5Z"/></svg><span>Explore LUNARIS</span>';
  document.body.append(link);
})();
