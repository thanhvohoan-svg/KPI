document.querySelectorAll('[data-common-form]').forEach(function(form){
 const inputs=Array.from(form.querySelectorAll('[data-common-score]'));
 const total=form.querySelector('[data-common-total]');
 function sum(){total.textContent=inputs.reduce((n,x)=>n+(Number(x.value)||0),0).toFixed(2);}
 inputs.forEach(x=>x.addEventListener('input',sum));
 form.addEventListener('invalid',function(e){const group=e.target.closest('details');if(group)group.open=true;},true);
 sum();
});
