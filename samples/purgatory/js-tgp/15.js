


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


console.log('Before test_vars, strA=' + strA);

function test_vars() {
  var strA = 'local strA';
  console.log('Inside test_vars, strA=' + strA);
}

test_vars();
console.log('After test_vars, strA=' + strA);


// This is now a js comment.

strC = /* inline comment FTW!!@#!@!! */ 'hullabaloo';

intD = 1;
while (intD < 4.25) {
  console.log('in while loop, intD=' + intD);
  intD += 1;
}
do {
  console.log('in do-while loop, intD=' + intD);
  intD += 1;
} while (intD < 4.25);

console.log('Checking op precedence, we should see 10 on the next line:');
console.log(3 + 4 * 5 % 13 || 42 && 912);

console.log(strA === 'function');
console.log(strA !== 'function');
console.log(100 === 1e2);
