
function print2nd(x, y) {
  console.log(y);
}

print2nd(123, 456);

print_twice = function (a) { print2nd(a, a); print2nd(a, a); }

print_twice('line 1\nline 2');

intA = 2384;
intB = +24;
intC = -1923;
boolA = !0;
strA = typeof print2nd;
strB = typeof {};

objA = {ilike: "pizza", butnot: 'eggs', '1729': true}

function yes_or_no(x) {
  if (x) {
    console.log('yes');
  } else {
    console.log('no');
  }
}

yes_or_no(objA['1729']);
yes_or_no(objA.ilike);

floatA = 3.141;
floatB = 6.022e23;

console.log(floatA);
console.log(floatB);
