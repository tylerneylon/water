


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


p = console.log;

p(/hello/.test('hello'));
p(/hello|there/.test('there'));
p(/hello|there/.test('their'));
p(/[abc][^abc]/.test('be'));
p(/[abc][^abc]/.test('ca'));
p(/\w\s\d/.test('a 3'));
p(/\w\s\d/.test('a a'));
p(/\bhi/.test('oh hi there'));
p(/\bhi/.test('this is cool'));
p(/a+b*c?d+/.test('aacd'));
p(/a+b*c?d+/.test('aabbbb'));
p(/(abc)(?:def)(?=ghi)/.test('abcdefghi'));
p(/(abc)(?:def)(?=ghi)/.test('abcdefgh'));
p(/hi/i.test('Hi'));
p(/hi/.test('Hi'));


function square (x) {
  return x * x;
}

arrayA = [1, 2, 3];
arrayB = [];
for (i = 0; i < arrayA.length; i += 1) {
  arrayB.push(square(arrayA[i]));
}
console.dir(arrayB);

n = 2;
switch(n) {
case 1:
  console.log('one');
  break;
case 2:
  console.log('two');
  // Fall through.
case 3:
  console.log('three');
  break;
case 4:
  console.log('four');
  break;
default:
  console.log('dinosaur');
}

function throwSomething() {
  throw "something";
}

function runAndCatch(fn) {
  try {
    fn();
  } catch (err) {
    console.log('I caught something:');
    console.log(err);
  }
}

function indirectlyThrowSomething() {
  throwSomething();
} 

runAndCatch(throwSomething);
runAndCatch(indirectlyThrowSomething);
